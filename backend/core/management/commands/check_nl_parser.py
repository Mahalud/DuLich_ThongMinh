import json
import os
from django.core.management.base import BaseCommand

from core.natural_language import parse_trip_query_gemini, parse_trip_query_rules, vietnam_today
from core.nl_query_examples import build_nl_query_samples


class Command(BaseCommand):
    help = 'Đánh giá bộ đọc câu tự nhiên bằng 20 câu mẫu; không warm-up embedding.'

    def handle(self, *args, **options):
        today = vietnam_today()
        samples = build_nl_query_samples(today)
        api_key = os.getenv('GEMINI_API_KEY')
        model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')
        fields = ('preference_labels', 'preference_text', 'budget_vnd', 'travel_date', 'weather_preference', 'duration_days', 'party_size', 'origin_text')
        rules_correct = rules_total = gemini_correct = gemini_total = 0
        heading = 'Câu | Quy tắc | Đúng trường (quy tắc) | Gemini | Đúng trường (Gemini)'
        self.stdout.write(f'Hôm nay theo giờ Việt Nam: {today:%d/%m/%Y}; {len(samples)} câu mẫu')
        self.stdout.write(heading)
        self.stdout.write('-' * 170)

        for sample in samples:
            query, expected = sample['query'], sample['expected']
            rule_result = parse_trip_query_rules(query, today=today)
            rule_ok = [field for field, expected_value in expected.items() if rule_result.get(field) == expected_value]
            rule_check = ','.join(f'{field}:{"đúng" if field in rule_ok else "sai"}' for field in expected)
            rules_total += len(expected)
            rules_correct += len(rule_ok)
            gemini_result = None
            if api_key:
                try:
                    gemini_result = parse_trip_query_gemini(query, today=today, api_key=api_key, model=model, timeout=8)
                    if gemini_result is None:
                        gemini_result = {'error': 'JSON không dùng được'}
                except Exception as exc:
                    gemini_result = {'error': type(exc).__name__}
            if isinstance(gemini_result, dict) and 'error' not in gemini_result:
                gemini_ok = [field for field, expected_value in expected.items() if gemini_result.get(field) == expected_value]
                gemini_total += len(expected)
                gemini_correct += len(gemini_ok)
                gemini_display = json.dumps({key: gemini_result.get(key) for key in fields}, ensure_ascii=False, separators=(',', ':'))
                gemini_check = ','.join(f'{field}:{"đúng" if field in gemini_ok else "sai"}' for field in expected)
            elif api_key:
                gemini_total += len(expected)
                gemini_display, gemini_check = f'lỗi {gemini_result.get("error", "không hợp lệ")}', ','.join(f'{field}:sai' for field in expected)
            else:
                gemini_display, gemini_check = '— (thiếu GEMINI_API_KEY)', '—'
            rule_display = json.dumps({key: rule_result.get(key) for key in fields}, ensure_ascii=False, separators=(',', ':'))
            self.stdout.write(f'{query} | {rule_display} | {rule_check} | {gemini_display} | {gemini_check}')

        self.stdout.write('')
        self.stdout.write(f'Độ đúng bộ quy tắc: {rules_correct}/{rules_total} trường ({100 * rules_correct / max(1, rules_total):.1f}%).')
        if api_key:
            self.stdout.write(f'Độ đúng Gemini: {gemini_correct}/{gemini_total} trường ({100 * gemini_correct / max(1, gemini_total):.1f}%).')
        else:
            self.stdout.write('Gemini chưa được chạy vì thiếu GEMINI_API_KEY.')

import json
import os

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.rag import build_rag_prompt, retrieve_knowledge, validate_rag_answer
from core.rag_examples import build_rag_examples


def _gemini_answer(question, chunks):
    key = os.getenv('GEMINI_API_KEY')
    if not key or not chunks:
        return None
    response = requests.post(
        f'https://generativelanguage.googleapis.com/v1beta/models/{os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")}:generateContent',
        params={'key': key},
        json={'contents': [{'parts': [{'text': build_rag_prompt(question, chunks)}]},],
              'generationConfig': {'temperature': 0.2, 'maxOutputTokens': 450}},
        timeout=10,
    )
    response.raise_for_status()
    candidates = response.json().get('candidates') or []
    return candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip() if candidates else ''


class Command(BaseCommand):
    help = 'Evaluate hybrid retrieval, refusal behavior, and optional Gemini answers; does not warm embeddings.'

    def handle(self, *args, **options):
        if not __import__('core.models', fromlist=['KnowledgeChunk']).KnowledgeChunk.objects.exists():
            raise CommandError('Knowledge index is empty. Run build_knowledge_index first.')
        examples = build_rag_examples()
        rows = []
        positive_scores, negative_scores = [], []
        recall_hits = recall_total = refusal_hits = refusal_total = 0
        self.stdout.write(f'Configured RAG_MIN_SIMILARITY={settings.RAG_MIN_SIMILARITY:.3f}; {len(examples)} examples')
        self.stdout.write('Question | Top 3 chunks (cosine) | Expected in top 3 | Retrieval/refusal check | Gemini answer')
        self.stdout.write('-' * 180)
        for example in examples:
            chunks = retrieve_knowledge(example['question'], limit=3, threshold=-1)
            expected_type = example['source_type']
            expected_title = example.get('title_contains')
            if expected_type is None:
                refusal_total += 1
                refused = not chunks
                refusal_hits += int(refused)
                if chunks:
                    negative_scores.append(chunks[0]['similarity'])
            else:
                recall_total += 1
                matched = any(
                    chunk['source_type'] == expected_type
                    and (not expected_title or expected_title in _fold(chunk['title']))
                    for chunk in chunks
                )
                found_expected = matched
                recall_hits += int(matched)
                expected_chunk = next((chunk for chunk in chunks
                                       if chunk['source_type'] == expected_type
                                       and (not expected_title or expected_title in _fold(chunk['title']))), None)
                if expected_chunk:
                    positive_scores.append(expected_chunk['similarity'])
            gemini_answer = ''
            if os.getenv('GEMINI_API_KEY') and chunks:
                try:
                    candidate = _gemini_answer(example['question'], chunks)
                    gemini_answer = candidate if validate_rag_answer(candidate, chunks) else '[REJECTED]'
                except Exception as exc:
                    gemini_answer = f'[{type(exc).__name__}]'
            top = '; '.join(f'[{chunk["n"]}] {chunk["title"]}={chunk["similarity"]:.3f}' for chunk in chunks)
            refusal_mark = 'correct refusal' if expected_type is None and not chunks else (
                'retrieval found source' if expected_type is not None and found_expected else
                'false retrieval' if expected_type is None else 'missed source'
            )
            rows.append((example['question'], [chunk['similarity'] for chunk in chunks], expected_type))
            if expected_type is None:
                expected_mark = 'n/a'
            else:
                expected_mark = 'yes' if found_expected else 'no'
            self.stdout.write(f'{example["question"]} | {top or "(no match)"} | {expected_mark} | {refusal_mark} | {gemini_answer}')

        threshold = _suggest_threshold(positive_scores, negative_scores, float(settings.RAG_MIN_SIMILARITY))
        self.stdout.write('')
        self.stdout.write(f'Recall@3 (answerable examples): {recall_hits}/{recall_total} ({100 * recall_hits / max(1, recall_total):.1f}%)')
        self.stdout.write(f'Correct refusal rate (unanswerable/out-of-scope): {refusal_hits}/{refusal_total} ({100 * refusal_hits / max(1, refusal_total):.1f}%)')
        self.stdout.write(f'Positive expected-chunk cosine scores: {json.dumps([round(value, 4) for value in positive_scores])}')
        self.stdout.write(f'Negative maximum cosine scores: {json.dumps([round(value, 4) for value in negative_scores])}')
        self.stdout.write(f'Suggested threshold on this sample: {threshold:.4f}')
        self.stdout.write('This sample threshold is diagnostic; review false positives and false negatives before changing settings.')


def _fold(value):
    from core.rag import normalize_for_match
    return normalize_for_match(value)


def _suggest_threshold(positives, negatives, current):
    candidates = sorted({current, *positives, *negatives})
    if not positives or not negatives:
        return current
    boundaries = [candidates[0] - 0.0001]
    boundaries.extend((left + right) / 2 for left, right in zip(candidates, candidates[1:]))
    boundaries.append(candidates[-1] + 0.0001)
    scored = []
    for threshold in boundaries:
        true_positive_rate = sum(score >= threshold for score in positives) / len(positives)
        false_positive_rate = sum(score >= threshold for score in negatives) / len(negatives)
        scored.append((true_positive_rate - false_positive_rate, threshold))
    return max(scored, key=lambda row: (row[0], row[1]))[1]

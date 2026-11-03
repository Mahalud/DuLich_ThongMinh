from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'BAO_CAO_DO_AN_CHUYEN_NGANH_BAN_THAO.docx'


def set_run_font(run, size=13, bold=None, italic=None):
    run.font.name = 'Times New Roman'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text, bold=False, size=11):
    cell.text = ''
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(str(text))
    set_run_font(run, size=size, bold=bold)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run()
    set_run_font(run, size=10)
    begin = OxmlElement('w:fldChar')
    begin.set(qn('w:fldCharType'), 'begin')
    instruction = OxmlElement('w:instrText')
    instruction.set(qn('xml:space'), 'preserve')
    instruction.text = ' PAGE '
    separate = OxmlElement('w:fldChar')
    separate.set(qn('w:fldCharType'), 'separate')
    text = OxmlElement('w:t')
    text.text = '1'
    end = OxmlElement('w:fldChar')
    end.set(qn('w:fldCharType'), 'end')
    run._r.extend([begin, instruction, separate, text, end])


def add_toc_field(paragraph):
    run = paragraph.add_run()
    set_run_font(run)
    begin = OxmlElement('w:fldChar')
    begin.set(qn('w:fldCharType'), 'begin')
    instruction = OxmlElement('w:instrText')
    instruction.set(qn('xml:space'), 'preserve')
    instruction.text = ' TOC \\o "1-3" \\h \\z \\u '
    separate = OxmlElement('w:fldChar')
    separate.set(qn('w:fldCharType'), 'separate')
    placeholder = OxmlElement('w:t')
    placeholder.text = 'Mở tài liệu bằng Word, chọn bảng mục lục và nhấn F9 để cập nhật.'
    end = OxmlElement('w:fldChar')
    end.set(qn('w:fldCharType'), 'end')
    run._r.extend([begin, instruction, separate, placeholder, end])


def add_paragraph(doc, text, style=None, align=None, first_line=True, italic=False):
    p = doc.add_paragraph(style=style)
    if align is not None:
        p.alignment = align
    if style is None:
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(3)
        if first_line:
            p.paragraph_format.first_line_indent = Cm(1)
    run = p.add_run(text)
    set_run_font(run, italic=italic)
    return p


def add_bullet(doc, text, numbered=False):
    p = doc.add_paragraph(style='List Number' if numbered else 'List Bullet')
    p.paragraph_format.line_spacing = 1.35
    p.paragraph_format.space_after = Pt(2)
    set_run_font(p.add_run(text))
    return p


def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(10 if level == 1 else 7)
    p.paragraph_format.space_after = Pt(5)
    for run in p.runs:
        set_run_font(run, size=16 if level == 1 else 13, bold=True)
    return p


def add_table(doc, headers, rows, widths=None, font_size=10):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for idx, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[idx], header, bold=True, size=font_size)
        set_cell_shading(table.rows[0].cells[idx], 'D9EAF7')
    for row in rows:
        cells = table.add_row().cells
        for idx, value in enumerate(row):
            set_cell_text(cells[idx], value, size=font_size)
    if widths:
        for row in table.rows:
            for idx, width in enumerate(widths):
                row.cells[idx].width = Cm(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def add_caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(7)
    set_run_font(p.add_run(text), size=11, italic=True)


def add_note_box(doc, text):
    table = doc.add_table(rows=1, cols=1)
    table.style = 'Table Grid'
    set_cell_shading(table.cell(0, 0), 'FFF2CC')
    set_cell_text(table.cell(0, 0), text, size=10)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def page_break(doc):
    doc.add_page_break()


def add_cover(doc, inner=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    for line, size in [
        ('TRƯỜNG ĐẠI HỌC TÀI NGUYÊN VÀ MÔI TRƯỜNG TP. HỒ CHÍ MINH', 16),
        ('KHOA CÔNG NGHỆ THÔNG TIN', 14),
    ]:
        r = p.add_run(line + '\n')
        set_run_font(r, size=size, bold=True)
    for _ in range(4):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for line in ['ĐỒ ÁN CHUYÊN NGÀNH CÔNG NGHỆ PHẦN MỀM', 'NGÀNH CÔNG NGHỆ THÔNG TIN']:
        r = p.add_run(line + '\n')
        set_run_font(r, size=16, bold=True)
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(20)
    r = p.add_run('XÂY DỰNG WEBSITE ĐẶT TOUR DU LỊCH\nTHÔNG MINH TÍCH HỢP AI')
    set_run_font(r, size=22, bold=True)
    for _ in range(3):
        doc.add_paragraph()
    for label, value in [
        ('Giảng viên hướng dẫn:', 'ThS. Nguyễn Duy Tuấn'),
        ('Sinh viên thực hiện:', 'Nguyễn Minh Tiến'),
        ('Mã số sinh viên:', '1250080196'),
        ('Lớp:', '12_ĐH_CNPM3'),
        ('Khóa:', '2023–2027'),
    ]:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(4)
        p.paragraph_format.space_after = Pt(3)
        set_run_font(p.add_run(f'{label}  {value}'), size=13, bold=label in {'Giảng viên hướng dẫn:', 'Lớp:'})
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(p.add_run('TP. Hồ Chí Minh, năm 2026'), size=13, bold=True)


def configure_main_section(section):
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2)
    section.header_distance = Cm(1)
    section.footer_distance = Cm(1)
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.LEFT
    header.paragraph_format.tab_stops.add_tab_stop(Cm(14))
    set_run_font(header.add_run('XÂY DỰNG WEBSITE ĐẶT TOUR DU LỊCH THÔNG MINH TÍCH HỢP AI\tThS. Nguyễn Duy Tuấn'), size=9)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.LEFT
    footer.paragraph_format.tab_stops.add_tab_stop(Cm(15.5))
    set_run_font(footer.add_run('Nguyễn Minh Tiến\t'), size=10)
    add_page_number(footer)
    sect_pr = section._sectPr
    page_numbering = OxmlElement('w:pgNumType')
    page_numbering.set(qn('w:start'), '1')
    sect_pr.append(page_numbering)


def build():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2)
    section.header_distance = Cm(1)
    section.footer_distance = Cm(1)

    styles = doc.styles
    normal = styles['Normal']
    normal.font.name = 'Times New Roman'
    normal._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    normal.font.size = Pt(13)
    normal.paragraph_format.line_spacing = 1.5
    for style_name in ['Heading 1', 'Heading 2', 'Heading 3']:
        style = styles[style_name]
        style.font.name = 'Times New Roman'
        style._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
        style.font.color.rgb = RGBColor(0, 0, 0)
    styles['Heading 1'].font.size = Pt(16)
    styles['Heading 2'].font.size = Pt(14)
    styles['Heading 3'].font.size = Pt(13)

    add_cover(doc)
    page_break(doc)
    add_cover(doc, inner=True)
    page_break(doc)

    add_heading(doc, 'LỜI CẢM ƠN', 1)
    add_paragraph(doc, 'Em xin chân thành cảm ơn ThS. Nguyễn Duy Tuấn đã hướng dẫn, góp ý và định hướng cho em trong quá trình thực hiện đồ án chuyên ngành. Những nhận xét của Thầy giúp em xác định phạm vi, lựa chọn phương pháp và hoàn thiện sản phẩm theo mục tiêu đã đề ra.', first_line=True)
    add_paragraph(doc, 'Em xin cảm ơn quý Thầy, Cô Khoa Công nghệ thông tin, Trường Đại học Tài nguyên và Môi trường TP. Hồ Chí Minh đã trang bị kiến thức nền tảng để em vận dụng vào đề tài. Em cũng cảm ơn gia đình, bạn bè đã động viên và hỗ trợ em trong quá trình học tập, thử nghiệm hệ thống và hoàn thiện báo cáo.', first_line=True)
    add_paragraph(doc, 'Do thời gian và kinh nghiệm còn hạn chế, báo cáo khó tránh khỏi thiếu sót. Em kính mong nhận được góp ý của quý Thầy, Cô để tiếp tục hoàn thiện đề tài.', first_line=True)
    p = doc.add_paragraph('\nSinh viên thực hiện\n\n\nNguyễn Minh Tiến')
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    page_break(doc)

    add_heading(doc, 'LỜI CAM ĐOAN', 1)
    add_paragraph(doc, 'Em cam đoan báo cáo này trình bày quá trình tìm hiểu, thiết kế và cài đặt đồ án “Xây dựng website đặt tour du lịch thông minh tích hợp AI” do em thực hiện dưới sự hướng dẫn của ThS. Nguyễn Duy Tuấn. Các nội dung kế thừa, số liệu, hình ảnh và tài liệu tham khảo từ nguồn khác được trích dẫn theo quy định. Các kết quả thử nghiệm trong báo cáo sẽ được bổ sung từ lần chạy thực tế và không được suy diễn hoặc tạo số liệu.', first_line=True)
    add_paragraph(doc, 'Em chịu trách nhiệm về tính trung thực của nội dung báo cáo và các minh chứng kèm theo.', first_line=True)
    p = doc.add_paragraph('\nSinh viên thực hiện\n(Ký và ghi rõ họ tên)\n\n\nNguyễn Minh Tiến')
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    page_break(doc)

    add_heading(doc, 'NHẬN XÉT CỦA GIẢNG VIÊN HƯỚNG DẪN', 1)
    for text in ['Kết cấu, phương pháp trình bày:', 'Cơ sở lý luận:', 'Tính thực tiễn và khả năng ứng dụng:', 'Kết quả đạt được:', 'Nội dung cần chỉnh sửa:']:
        add_paragraph(doc, text + '\n\n\n', first_line=False)
    add_paragraph(doc, 'Kết luận:  ☐ Đồng ý cho sinh viên nộp báo cáo    ☐ Không đồng ý', first_line=False)
    add_paragraph(doc, '\nGiảng viên hướng dẫn\n(Ký và ghi rõ họ tên)', align=WD_ALIGN_PARAGRAPH.RIGHT, first_line=False)
    page_break(doc)

    add_heading(doc, 'NHẬN XÉT CỦA NGƯỜI PHẢN BIỆN', 1)
    for _ in range(8):
        add_paragraph(doc, '............................................................................................................................', first_line=False)
    add_paragraph(doc, 'Kết luận:  ☐ Đồng ý cho sinh viên nộp báo cáo    ☐ Không đồng ý', first_line=False)
    add_paragraph(doc, '\nNgười phản biện\n(Ký và ghi rõ họ tên)', align=WD_ALIGN_PARAGRAPH.RIGHT, first_line=False)
    page_break(doc)

    add_heading(doc, 'LỊCH LÀM VIỆC', 1)
    schedule_rows = [
        ('Tuần 1–3', '24/08–13/09/2026', 'Đăng ký đề tài, khảo sát tài liệu và hoàn thiện đề cương.'),
        ('Tuần 4', '14/09–20/09/2026', 'Khảo sát nghiệp vụ, xác định yêu cầu, thiết kế dữ liệu và giao diện.'),
        ('Tuần 5', '21/09–27/09/2026', 'Cài đặt môi trường; xây dựng tài khoản, hồ sơ và tích hợp thời tiết.'),
        ('Tuần 6', '28/09–04/10/2026', 'Xây dựng điểm đến và thuật toán gợi ý đa tiêu chí.'),
        ('Tuần 7', '05/10–11/10/2026', 'Xây dựng quản trị tour/chỗ ở/phòng và luồng đặt chỗ.'),
        ('Tuần 8', '12/10–18/10/2026', 'Tích hợp thanh toán sandbox, bản đồ, PostGIS và hoàn thiện giao diện.'),
        ('Tuần 9–10', '19/10–01/11/2026', 'Kiểm thử chức năng, tích hợp, hiệu năng và chất lượng gợi ý.'),
        ('Tuần 11', '02/11–08/11/2026', 'Hoàn thiện dashboard, chat realtime, bản tin và báo cáo.'),
        ('Tuần 12–15', '09/11–06/12/2026', 'Viết, hiệu chỉnh báo cáo, chuẩn bị slide và trình bày theo lịch Khoa.'),
    ]
    add_table(doc, ['Giai đoạn', 'Thời gian', 'Nội dung'], schedule_rows, font_size=10)
    add_note_box(doc, 'Bảng lịch này được lấy từ đề cương đã duyệt. Cập nhật cột kết quả/thời gian thực tế nếu GVHD yêu cầu nêu tiến độ hoàn thành.')
    page_break(doc)

    add_heading(doc, 'TÓM TẮT ĐỒ ÁN', 1)
    add_paragraph(doc, 'Đồ án xây dựng website hỗ trợ tìm kiếm điểm đến, lập hành trình và đặt tour/chỗ ở, hướng đến người dùng cần cân nhắc đồng thời sở thích, ngân sách, thời tiết dự kiến và khoảng cách. Frontend được phát triển bằng React; backend dùng Django REST Framework; dữ liệu quan hệ được lưu trên PostgreSQL/PostGIS. Redis và Celery hỗ trợ cache và tác vụ nền; Django Channels cung cấp chat thời gian thực.', first_line=True)
    add_paragraph(doc, 'Thuật toán gợi ý biểu diễn sở thích bằng embedding Sentence-BERT và so khớp cosine; chấm điểm thời tiết bằng logic mờ; chấm ngân sách bằng hàm tuyến tính; tính khoảng cách bằng Haversine; tổng hợp bằng Weighted Sum Model. Các tiêu chí không được người dùng cung cấp được loại khỏi phép tổng hợp và trọng số còn lại được chuẩn hóa. Gemini được dùng để diễn giải kết quả sau khi xếp hạng; nội dung được kiểm tra và có giải thích dự phòng.', first_line=True)
    add_paragraph(doc, 'Hệ thống còn có tìm chỗ ở theo bán kính bằng PostGIS, hiển thị tuyến đường trên Leaflet, quản lý và đặt phòng/tour, thanh toán VNPay/MoMo sandbox, cộng đồng, đánh giá, trợ lý RAG, chat và khu quản trị. Dữ liệu tour và chỗ ở là dữ liệu minh họa. Kết quả kiểm thử định lượng và ảnh minh chứng sẽ được cập nhật sau khi chạy toàn bộ kịch bản trên phiên bản chốt.', first_line=True)
    add_paragraph(doc, 'Từ khóa: hệ thống gợi ý; Sentence-BERT; logic mờ; Weighted Sum Model; PostGIS; Django; React.', first_line=False)
    page_break(doc)

    add_heading(doc, 'MỤC LỤC', 1)
    add_toc_field(doc.add_paragraph())
    page_break(doc)

    add_heading(doc, 'DANH MỤC SƠ ĐỒ, HÌNH', 1)
    for item in ['Sơ đồ 2.1. Kiến trúc tổng thể của hệ thống', 'Sơ đồ 2.2. Luồng xử lý gợi ý điểm đến', 'Sơ đồ 2.3. Luồng đặt phòng và xác nhận thanh toán', 'Sơ đồ 2.4. Quan hệ các nhóm thực thể chính', 'Hình 3.1. Trang chủ và biểu mẫu tìm gợi ý [bổ sung ảnh]', 'Hình 3.2. Danh sách kết quả gợi ý [bổ sung ảnh]', 'Hình 3.3. Trang chi tiết điểm đến và bản đồ [bổ sung ảnh]', 'Hình 3.4. Luồng đặt phòng/tour [bổ sung ảnh]', 'Hình 3.5. Chat realtime user-admin [bổ sung ảnh]']:
        add_paragraph(doc, item, first_line=False)
    page_break(doc)

    add_heading(doc, 'DANH MỤC BẢNG BIỂU', 1)
    for item in ['Bảng 1.1. So sánh nhóm phương pháp gợi ý liên quan', 'Bảng 2.1. Yêu cầu chức năng', 'Bảng 2.2. Yêu cầu phi chức năng', 'Bảng 2.3. Các thực thể và quan hệ chính', 'Bảng 2.4. Trọng số mặc định của các tiêu chí', 'Bảng 3.1. Môi trường cài đặt', 'Bảng 3.2. Kịch bản kiểm thử chức năng', 'Bảng 3.3. Kết quả kiểm thử tự động [điền số thực tế]', 'Bảng 3.4. Kết quả đo thời gian phản hồi [điền số thực tế]', 'Bảng 3.5. Ví dụ minh họa tính điểm']:
        add_paragraph(doc, item, first_line=False)
    page_break(doc)

    add_heading(doc, 'DANH MỤC TỪ VIẾT TẮT', 1)
    add_table(doc, ['Từ viết tắt', 'Tên đầy đủ', 'Diễn giải'], [
        ('AI', 'Artificial Intelligence', 'Trí tuệ nhân tạo'),
        ('API', 'Application Programming Interface', 'Giao diện lập trình ứng dụng'),
        ('DRF', 'Django REST Framework', 'Bộ công cụ xây dựng REST API cho Django'),
        ('GIS', 'Geographic Information System', 'Hệ thống thông tin địa lý'),
        ('LLM', 'Large Language Model', 'Mô hình ngôn ngữ lớn'),
        ('NLP', 'Natural Language Processing', 'Xử lý ngôn ngữ tự nhiên'),
        ('RAG', 'Retrieval-Augmented Generation', 'Sinh câu trả lời có tăng cường truy xuất'),
        ('REST', 'Representational State Transfer', 'Kiểu kiến trúc API web'),
        ('SBERT', 'Sentence-BERT', 'Mô hình embedding câu dựa trên BERT'),
        ('WSM', 'Weighted Sum Model', 'Mô hình tổng trọng số'),
    ])
    doc.add_section(WD_SECTION.NEW_PAGE)
    configure_main_section(doc.sections[-1])
    add_heading(doc, 'MỞ ĐẦU', 1)
    add_heading(doc, '1. Lý do chọn đề tài', 2)
    add_paragraph(doc, 'Nhu cầu du lịch tự túc đặt ra bài toán lựa chọn điểm đến trong điều kiện nhiều tiêu chí: sở thích, ngân sách, thời tiết tại thời điểm dự kiến đi và khoảng cách từ vị trí xuất phát. Khi thông tin nằm rải rác ở nhiều nguồn, người dùng phải tự tổng hợp và khó so sánh phương án. Các hệ thống gợi ý theo ngữ cảnh và đa tiêu chí là một hướng tiếp cận đã được nghiên cứu trong du lịch thông minh [1], [2].')
    add_paragraph(doc, 'Đề tài lựa chọn xây dựng một website kết hợp mô hình embedding ngữ nghĩa, logic mờ và tổng trọng số để đưa ra thứ hạng có thể giải thích. Hệ thống tiếp tục nối kết quả tìm kiếm với quy trình đặt tour, đặt chỗ ở, thanh toán thử nghiệm, bản đồ và trao đổi hỗ trợ trên cùng một nền tảng.')
    add_heading(doc, '2. Mục tiêu', 2)
    for text in [
        'Xây dựng website client–server với giao diện React và backend Django REST Framework.',
        'Cài đặt thuật toán xếp hạng điểm đến từ sở thích, thời tiết, ngân sách và khoảng cách; cho phép loại tiêu chí không có đầu vào.',
        'Tích hợp giải thích ngôn ngữ tự nhiên, trợ lý truy xuất tri thức, bản đồ, tìm chỗ ở quanh điểm đến và lập kế hoạch.',
        'Xây dựng nghiệp vụ tài khoản, quản trị, đặt phòng/tour, tồn kho, thanh toán sandbox, hủy/hoàn, đánh giá, cộng đồng và chat.',
        'Kiểm thử chức năng và đo kết quả thực nghiệm trên dữ liệu được quản trị; phân biệt rõ dữ liệu minh họa với dữ liệu dịch vụ thật.',
    ]:
        add_bullet(doc, text)
    add_heading(doc, '3. Đối tượng và phạm vi', 2)
    add_paragraph(doc, 'Đối tượng gồm người dùng tìm kiếm du lịch; các phương pháp Sentence-BERT, cosine similarity, logic mờ, WSM, Haversine và PostGIS; cùng các nghiệp vụ quản lý/đặt tour, chỗ ở và thanh toán. Phạm vi địa lý của dữ liệu gợi ý là Việt Nam; dự báo thời tiết giới hạn tối đa 16 ngày. Đề tài sử dụng mô hình pretrained, không huấn luyện một mô hình ngôn ngữ mới từ đầu.')
    add_paragraph(doc, 'Địa danh, tọa độ và địa chỉ được tra cứu qua Nominatim; ảnh minh họa điểm đến lấy từ dịch vụ ảnh theo cấu hình dự án. Chỗ ở, loại phòng và tour là dữ liệu demo do quản trị viên biên soạn, không đại diện cho cơ sở lưu trú hoặc tour thương mại có thật. Thanh toán dùng sandbox, không phát sinh thu tiền thật.')
    add_heading(doc, '4. Phương pháp nghiên cứu', 2)
    add_paragraph(doc, 'Phương pháp lý thuyết gồm tổng hợp tài liệu về hệ thống gợi ý, NLP, logic mờ, ra quyết định đa tiêu chí, GIS và kiến trúc web. Phương pháp thực nghiệm gồm phân tích yêu cầu, thiết kế, cài đặt theo module, tích hợp dịch vụ, kiểm thử luồng nghiệp vụ và đánh giá định lượng/định tính. Các số liệu đánh giá phải được lấy từ lần chạy thực tế của bản chốt.')
    add_heading(doc, '5. Bố cục báo cáo', 2)
    add_paragraph(doc, 'Chương 1 trình bày tổng quan tài liệu, cơ sở lý thuyết và công nghệ. Chương 2 trình bày yêu cầu, thiết kế dữ liệu, kiến trúc và thuật toán. Chương 3 mô tả cài đặt, kiểm thử, kết quả và đánh giá. Cuối báo cáo là kết luận, hướng phát triển, phụ lục và tài liệu tham khảo.')

    page_break(doc)
    add_heading(doc, 'CHƯƠNG 1: TỔNG QUAN TÀI LIỆU', 1)
    add_heading(doc, '1.1. Khảo sát bài toán và các hướng tiếp cận', 2)
    add_paragraph(doc, 'Hệ thống gợi ý du lịch cần xử lý dữ liệu đa dạng và có tính thời gian. Một nhóm nghiên cứu khai thác ngữ cảnh như thời tiết và khoảng cách để hỗ trợ lựa chọn điểm đến [1]. Một hướng khác dùng logic mờ cho cá nhân hóa và ra quyết định đa tiêu chí nhằm xử lý các khái niệm không có ranh giới tuyệt đối [2]. Các nghiên cứu về mạng ngôn ngữ và dữ liệu đa phương thức khảo sát khả năng cá nhân hóa trên quy mô dữ liệu lớn [4], [5].')
    add_paragraph(doc, 'Đề tài này chọn cấu hình có thể giải thích, triển khai ở quy mô đồ án và nối trực tiếp với nghiệp vụ web. Điểm khác biệt về thiết kế là đưa ngôn ngữ tự do vào embedding sở thích, kết hợp thời tiết/ngân sách/khoảng cách trong một điểm xếp hạng, rồi nối sang đặt chỗ, thanh toán sandbox, bản đồ và các chức năng hỗ trợ.')
    add_table(doc, ['Hướng tiếp cận', 'Ưu điểm', 'Hạn chế cần lưu ý', 'Cách đề tài sử dụng'], [
        ('Tìm theo bộ lọc cứng', 'Dễ cài đặt, giải thích đơn giản.', 'Không hiểu diễn đạt ngữ nghĩa; khó tổng hợp nhiều tiêu chí mềm.', 'Dùng cho kiểm tra dữ liệu/range, không làm bộ xếp hạng duy nhất.'),
        ('Embedding + cosine', 'So sánh ý nghĩa câu và mô tả.', 'Phụ thuộc chất lượng mô tả, mô hình và ngưỡng.', 'Dùng cho mức tương đồng sở thích.'),
        ('Logic mờ', 'Điểm thay đổi liên tục, phù hợp khái niệm chủ quan.', 'Cần chọn membership function và trọng số hợp lý.', 'Dùng cho nhiệt độ, mưa và gió.'),
        ('WSM', 'Minh bạch, dễ kiểm tra đóng góp từng tiêu chí.', 'Nhạy với chuẩn hóa và trọng số.', 'Tổng hợp điểm thành phần đã đưa về thang 0–1.'),
        ('RAG + LLM', 'Sinh câu trả lời ngôn ngữ tự nhiên có nguồn.', 'Có thể sai nếu thiếu bằng chứng hoặc prompt không chặt.', 'Truy xuất chunk, kiểm tra nguồn/số, dùng fallback.'),
    ], font_size=9)
    add_caption(doc, 'Bảng 1.1. So sánh các nhóm phương pháp liên quan')

    add_heading(doc, '1.2. Cơ sở lý thuyết', 2)
    add_heading(doc, '1.2.1. Sentence-BERT và độ tương đồng cosine', 3)
    add_paragraph(doc, 'Sentence-BERT tạo biểu diễn vector cho câu, cho phép so sánh câu bằng cosine similarity thay vì so từng từ [3]. Với vector A và B, cosine bằng tích vô hướng chia cho tích độ dài hai vector. Khi vector đã chuẩn hóa, phép đo phản ánh mức cùng hướng. Giá trị dùng để xếp hạng tương đồng, không phải xác suất người dùng chắc chắn thích địa điểm.')
    add_heading(doc, '1.2.2. Logic mờ', 3)
    add_paragraph(doc, 'Logic mờ biểu diễn mức độ một giá trị thuộc tập khái niệm bằng số trong [0,1], thay vì chỉ đúng/sai [2], [5]. Hàm hình thang có vùng tăng tuyến tính, vùng đỉnh đạt 1 và vùng giảm tuyến tính. Trong hệ thống, nhiệt độ được chấm theo các mốc cấu hình; xác suất mưa thấp và gió thấp cho mức phù hợp cao hơn.')
    add_heading(doc, '1.2.3. Chấm điểm tuyến tính ngân sách', 3)
    add_paragraph(doc, 'Chi phí tham khảo không vượt ngân sách nhận điểm 1. Khi vượt ngân sách, điểm giảm theo tỷ lệ phần vượt: `max(0, 1 − (Cost − Budget)/Budget)`. Nếu ngân sách không được cung cấp, hệ thống bỏ tiêu chí thay vì diễn giải số 0 là giới hạn chi tiêu.')
    add_heading(doc, '1.2.4. Haversine và truy vấn không gian', 3)
    add_paragraph(doc, 'Haversine ước lượng khoảng cách cung tròn giữa hai tọa độ trên mặt cầu. PostGIS mở rộng PostgreSQL để lưu và truy vấn dữ liệu không gian, có thể lọc đối tượng trong bán kính và tận dụng spatial index [11], [12]. Trong hệ thống, Haversine dùng chấm độ thuận tiện xuất phát; PostGIS dùng tìm chỗ ở quanh điểm đến; OpenRouteService cung cấp geometry đường bộ khi có tuyến.')
    add_heading(doc, '1.2.5. Weighted Sum Model', 3)
    add_paragraph(doc, 'WSM nhân từng điểm tiêu chí chuẩn hóa với trọng số tương ứng rồi cộng lại. Tính minh bạch cho phép trình bày từng đóng góp, nhưng kết quả phụ thuộc cách chuẩn hóa, trọng số và tính đầy đủ dữ liệu.')
    add_heading(doc, '1.2.6. Celery, Redis và RAG', 3)
    add_paragraph(doc, 'Celery chạy tác vụ ngoài request/response; Redis làm broker, backend kết quả, cache và channel layer tùy cấu hình. RAG truy xuất các đoạn tri thức liên quan rồi cung cấp chúng làm bằng chứng cho mô hình sinh [14]. Đề tài kiểm tra số liệu/citation và có hướng trả lời trích xuất khi nội dung sinh không hợp lệ.')

    add_heading(doc, '1.3. Công nghệ sử dụng', 2)
    add_table(doc, ['Công nghệ', 'Vai trò'], [
        ('React + Vite', 'Giao diện thành phần, điều hướng và build frontend.'),
        ('Django + Django REST Framework', 'API, xác thực, quy tắc nghiệp vụ và thuật toán.'),
        ('PostgreSQL + PostGIS / GeoDjango', 'Dữ liệu nghiệp vụ, tọa độ, geometry và lọc bán kính.'),
        ('Redis + Celery', 'Cache, hàng đợi và tác vụ nền.'),
        ('Django Channels + Daphne', 'WebSocket chat realtime.'),
        ('Leaflet + OpenStreetMap', 'Bản đồ nền và hiển thị geometry.'),
        ('Open-Meteo, Nominatim, OpenRouteService', 'Thời tiết, tìm địa danh, tuyến đường.'),
        ('Sentence-Transformers, Gemini API', 'Embedding ngữ nghĩa và diễn giải/RAG có kiểm soát.'),
        ('VNPay/MoMo Sandbox', 'Thử nghiệm luồng tạo giao dịch, callback và refund.'),
        ('Docker Compose', 'Đóng gói và vận hành các dịch vụ phát triển.'),
    ], font_size=10)

    page_break(doc)
    add_heading(doc, 'CHƯƠNG 2: PHƯƠNG PHÁP THỰC HIỆN', 1)
    add_heading(doc, '2.1. Phân tích yêu cầu hệ thống', 2)
    add_paragraph(doc, 'Các tác nhân chính là khách chưa đăng nhập, người dùng đã đăng nhập và quản trị viên. Khách có thể xem nội dung công khai và thử gợi ý; người dùng có thể lưu hồ sơ, xem lịch sử, đặt dịch vụ, đánh giá đủ điều kiện, đăng cộng đồng và chat; quản trị viên quản lý dữ liệu, đơn hàng và nội dung.')
    add_table(doc, ['Mã', 'Yêu cầu chức năng', 'Tác nhân'], [
        ('FR-01', 'Đăng ký, đăng nhập, đăng xuất, khôi phục và đổi mật khẩu.', 'Khách / người dùng'),
        ('FR-02', 'Nhập tiêu chí và nhận điểm đến xếp hạng kèm điểm thành phần.', 'Khách / người dùng'),
        ('FR-03', 'Lưu hồ sơ, lịch sử tìm kiếm và tùy chọn thời tiết.', 'Người dùng'),
        ('FR-04', 'Xem điểm đến, thời tiết, bản đồ, tuyến đường và chỗ ở gần.', 'Mọi người'),
        ('FR-05', 'Lập hành trình cá nhân nhiều điểm.', 'Người dùng'),
        ('FR-06', 'Xem tour/lịch khởi hành, đặt tour; chọn loại phòng và đặt phòng.', 'Người dùng'),
        ('FR-07', 'Khởi tạo thanh toán sandbox, nhận callback/IPN và xem trạng thái.', 'Người dùng / cổng'),
        ('FR-08', 'Hủy đơn theo chính sách; quản lý hoàn tiền.', 'Người dùng / admin'),
        ('FR-09', 'Chat realtime, cộng đồng và đánh giá sau lưu trú.', 'Người dùng / admin'),
        ('FR-10', 'CRUD dữ liệu du lịch, nội dung và xem thống kê.', 'Admin'),
        ('FR-11', 'Trả lời câu hỏi du lịch dựa trên tri thức công khai (RAG).', 'Khách / người dùng'),
    ], font_size=9)
    add_caption(doc, 'Bảng 2.1. Yêu cầu chức năng chính')
    add_table(doc, ['Nhóm', 'Yêu cầu phi chức năng'], [
        ('Bảo mật', 'Kiểm tra phiên, quyền staff, quyền sở hữu; CSRF cho thao tác cookie; mã hóa số điện thoại; bảo vệ secret qua môi trường.'),
        ('Tính đúng đắn', 'Tính tiền trên server; xác thực chữ ký callback; giới hạn chỗ trong transaction.'),
        ('Khả dụng', 'Lỗi dịch vụ thời tiết/LLM có fallback; tác vụ nền có trạng thái; frontend có loading/error/empty states.'),
        ('Hiệu năng', 'Cache dự báo, gọi thời tiết song song, xử lý tác vụ chậm nền; cần bổ sung benchmark thực tế.'),
        ('Khả năng sử dụng', 'Giao diện tiếng Việt, responsive, hiển thị điểm thành phần và chính sách đơn.'),
        ('Khả năng bảo trì', 'Tách frontend/backend/API, model/serializer/task; Docker Compose cho môi trường phát triển.'),
    ], font_size=9)
    add_caption(doc, 'Bảng 2.2. Yêu cầu phi chức năng')

    add_heading(doc, '2.2. Thiết kế dữ liệu', 2)
    add_paragraph(doc, 'Cơ sở dữ liệu tổ chức quanh các nhóm tài khoản, gợi ý, điểm đến, chỗ ở, tour, đặt chỗ, thanh toán, cộng đồng và chat. Một số quan hệ một-nhiều: Destination–Accommodation, Accommodation–RoomType, Tour–TourStop, Tour–TourDeparture. Booking nối User–RoomType; TourBooking nối User–TourDeparture. AccommodationReview có thể gắn một-một với Booking để đảm bảo mỗi đơn chỉ có một đánh giá.')
    add_table(doc, ['Thực thể', 'Thuộc tính tiêu biểu', 'Quan hệ/nghiệp vụ'], [
        ('Destination', 'Tên, category, mô tả, address, lat/lon, reference_cost, rating, embedding.', 'Có nhiều Accommodation, TourStop, SearchHistory, feedback.'),
        ('Accommodation', 'Tên, mô tả, category, tọa độ, rating.', 'Thuộc Destination; có RoomType và Review.'),
        ('RoomType', 'Tên, giá đêm, stock, danh sách amenity keys.', 'Thuộc Accommodation; được đặt bởi Booking.'),
        ('Booking', 'User, RoomType, check-in/out, phone mã hóa, status, payment/refund fields.', 'Đơn phòng và căn cứ đánh giá.'),
        ('Tour / TourStop / TourDeparture', 'Mô tả, giá, ngày trong lịch trình, ngày khởi hành, slots_total.', 'Tour có các điểm dừng và ngày khởi hành.'),
        ('TourBooking', 'Departure, số người, giá, phone mã hóa, trạng thái.', 'Đơn đặt tour và trừ chỗ theo departure.'),
        ('ChatMessage', 'Conversation user, sender, content, attachment, is_read, created_at.', 'Hội thoại riêng mỗi người dùng; admin có thể tham gia.'),
        ('KnowledgeChunk', 'Source, title, content, URL, metadata, hash, embedding.', 'Cơ sở truy xuất trợ lý RAG.'),
    ], font_size=9)
    add_caption(doc, 'Bảng 2.3. Các thực thể chính và vai trò')
    add_note_box(doc, 'Khi hoàn thiện cần chèn ERD xuất từ schema/migration thực tế. Không vẽ quan hệ không có trong model; ảnh ERD là Hình 2.4.')

    add_heading(doc, '2.3. Kiến trúc hệ thống', 2)
    add_paragraph(doc, 'Hệ thống chia thành giao diện SPA và backend API. React gọi DRF qua HTTP; WebSocket được phục vụ bởi Daphne/Channels. Backend truy cập PostgreSQL/PostGIS; Redis phục vụ Celery và channel layer. Các API ngoài được gọi ở các điểm cần thiết: Open-Meteo cho thời tiết, Nominatim cho địa danh, OpenRouteService cho route, Gemini cho phần sinh ngôn ngữ. Thanh toán chỉ gọi khi người dùng chọn cổng.')
    add_table(doc, ['Lớp', 'Thành phần', 'In/Out'], [
        ('Giao diện', 'React pages/components, auth context, origin context.', 'Nhận nhập liệu; gọi API; hiển thị trạng thái và kết quả.'),
        ('API/nghiệp vụ', 'Django REST Framework, serializers, permissions, views.', 'Validate request; gọi service; kiểm tra quyền; đọc/ghi model.'),
        ('Tác vụ nền', 'Celery tasks qua Redis broker.', 'Nhận task id; xử lý embedding/LLM/cache; lưu kết quả.'),
        ('Realtime', 'Channels consumer + Redis channel layer.', 'Xác thực socket; lưu/broadcast tin và unread event.'),
        ('Lưu trữ', 'PostgreSQL/PostGIS; Redis cache.', 'Dữ liệu lâu dài/không gian; cache và hàng đợi.'),
        ('Tích hợp', 'Open-Meteo, Nominatim, ORS, Gemini, VNPay, MoMo.', 'Dữ liệu dự báo/địa danh/route; giải thích; giao dịch test.'),
    ], font_size=9)
    add_caption(doc, 'Bảng 2.4. Phân lớp và luồng trao đổi dữ liệu')
    add_paragraph(doc, 'Sơ đồ kiến trúc gợi ý để thay bằng hình vẽ vector trong bản hoàn thiện:', first_line=False, italic=True)
    add_paragraph(doc, 'Người dùng → React/Vite → Django REST API → PostgreSQL/PostGIS\n                                     ↘ Redis ↔ Celery worker → Gemini / Sentence-BERT\nReact ⇄ WebSocket / Django Channels ⇄ Redis channel layer\nDjango → Open-Meteo / Nominatim / OpenRouteService / VNPay / MoMo', first_line=False)
    add_caption(doc, 'Sơ đồ 2.1. Kiến trúc tổng thể (bản mô tả, cần thay bằng hình minh họa rõ ràng)')

    add_heading(doc, '2.4. Thiết kế thuật toán gợi ý', 2)
    add_heading(doc, '2.4.1. Tiền xử lý truy vấn sở thích', 3)
    add_paragraph(doc, 'Chuỗi được cắt khoảng trắng, bỏ ký tự điều khiển và giới hạn tối đa 200 ký tự. Nhãn như “biển”, “núi”, “ẩm thực”, “văn hóa”, “nghỉ dưỡng” được mở rộng thành mô tả ngữ nghĩa giàu ngữ cảnh trước khi encode. Văn bản điểm đến ghép tên, category, địa chỉ và mô tả. Việc cải thiện chất lượng mô tả giúp giảm nguy cơ vector không phản ánh đủ đặc điểm địa điểm.')
    add_heading(doc, '2.4.2. Điểm sở thích', 3)
    add_paragraph(doc, 'Gọi `encode_text()` cho truy vấn và so với embedding điểm đến bằng cosine. Nếu truy vấn rỗng, tiêu chí bị loại. Nếu cosine tối đa thấp hơn ngưỡng `PREFERENCE_MATCH_MIN`, hệ thống không kéo giãn min-max; giữ mức raw thấp, đặt `preference_matched=false` và giải thích rằng không thấy khớp rõ. Nếu có khớp, min-max chuẩn hóa trong tập ứng viên; khi các giá trị đều bằng nhau, dùng điểm trung tính theo xử lý của hệ thống.')
    add_heading(doc, '2.4.3. Điểm thời tiết', 3)
    add_paragraph(doc, 'Dự báo theo ngày gồm nhiệt độ cao nhất, xác suất mưa và gió lớn nhất. Với cân bằng, nhiệt độ có hình thang 15–24–30–40 °C và trọng số nhiệt/mưa/gió lần lượt 0,5/0,3/0,2. Chế độ mát chuyển mốc thành 12–16–24–30; nắng ấm thành 24–28–33–40; ít mưa giữ mốc nhiệt cân bằng và chuyển trọng số thành 0,3/0,5/0,2. Cache lưu số liệu thô, không lưu điểm đã tính.')
    add_heading(doc, '2.4.4. Điểm ngân sách và khoảng cách', 3)
    add_paragraph(doc, 'Chi phí tham khảo lấy từ reference_cost của từng điểm đến; nếu chưa khai báo thì dùng mức mặc định theo category. Ngân sách 0/rỗng thì loại tiêu chí. Khoảng cách xuất phát dùng Haversine với R≈6371 km; `Distance_Score = 1 − min(d/DISTANCE_MAX_KM, 1)`, mặc định dmax=1000 km. Không có tọa độ xuất phát thì distance_score là null và trọng số tương ứng được loại.')
    add_heading(doc, '2.4.5. Tổng hợp và trọng số', 3)
    add_paragraph(doc, 'Trọng số mặc định lần lượt là 0,40 cho sở thích, 0,25 cho thời tiết, 0,20 cho ngân sách, 0,15 cho khoảng cách. Tổng điểm là tổng tích trọng số và điểm thành phần. Khi tiêu chí vắng, hệ thống loại trọng số của tiêu chí đó và chuẩn hóa các trọng số còn lại. Khi đủ phản hồi đặt/bỏ qua, thuật toán cập nhật trọng số từng bước 0,02 trong các giới hạn cấu hình.')
    add_table(doc, ['Trường hợp minh họa', 'Preference', 'Weather', 'Budget', 'Distance', 'Điểm tổng'], [
        ('Đủ bốn tiêu chí, điểm ví dụ', '0,90', '0,82', '1,00', '0,75', '0,8775 (87,75%)'),
    ], font_size=10)
    add_caption(doc, 'Bảng 2.5. Ví dụ số học minh họa; không phải kết quả đo thực tế')
    add_paragraph(doc, 'Tính: 0,40×0,90 + 0,25×0,82 + 0,20×1,00 + 0,15×0,75 = 0,8775. Trong báo cáo cuối, cần thay bằng một response thật được lưu làm minh chứng và ghi rõ bộ đầu vào tương ứng.')

    add_heading(doc, '2.5. Thiết kế giao diện', 2)
    add_paragraph(doc, 'Giao diện tổ chức thành trang chủ, gợi ý, chi tiết điểm đến, kế hoạch, tour, chỗ ở, hồ sơ, trợ lý, cộng đồng, chat và khu quản trị. Các trang dùng hệ thống màu/chữ và component dùng chung; bố cục thay đổi theo màn hình. Trạng thái tải, rỗng, lỗi API và quyền truy cập được thể hiện riêng. Bản chốt cần bổ sung ảnh giao diện tại các kích thước 375, 768 và 1280 px nếu Khoa/GVHD yêu cầu minh chứng responsive.')

    page_break(doc)
    add_heading(doc, 'CHƯƠNG 3: CÀI ĐẶT THỰC NGHIỆM, KẾT QUẢ VÀ ĐÁNH GIÁ', 1)
    add_heading(doc, '3.1. Môi trường và triển khai', 2)
    add_table(doc, ['Thành phần', 'Cấu hình/phần mềm'], [
        ('Hệ điều hành phát triển', 'Windows 11 (máy phát triển cá nhân) — xác nhận lại phiên bản.'),
        ('Backend', 'Python 3.12, Django, Django REST Framework, Django Channels, Celery.'),
        ('Frontend', 'React, Vite, JavaScript, Leaflet.'),
        ('Cơ sở dữ liệu', 'PostgreSQL với PostGIS; cấu hình phát triển qua Docker Compose.'),
        ('Cache / broker', 'Redis.'),
        ('Dịch vụ ngoài', 'Open-Meteo, Nominatim, OpenRouteService, Gemini; VNPay/MoMo Sandbox.'),
        ('Trình duyệt thử nghiệm', '[điền tên và phiên bản trình duyệt thực tế].'),
        ('Commit/version thử nghiệm', '[điền mã commit và ngày chốt].'),
    ], font_size=10)
    add_caption(doc, 'Bảng 3.1. Môi trường cài đặt; cần xác nhận phiên bản trước khi nộp')
    add_paragraph(doc, 'Ứng dụng được chia thành frontend và các dịch vụ backend. Trong môi trường phát triển, Docker Compose chạy cơ sở dữ liệu, Redis, backend và Celery; Vite chạy giao diện. Có thể mở truy cập ngoài mạng qua Cloudflare Tunnel phục vụ demo, nhưng tunnel tới máy cá nhân không được xem là hạ tầng production liên tục.')

    add_heading(doc, '3.2. Các module đã cài đặt', 2)
    module_rows = [
        ('Tài khoản', 'Đăng ký/đăng nhập, hồ sơ, đặt lại/đổi mật khẩu, kiểm tra quyền.'),
        ('Gợi ý', 'Embedding sở thích, thời tiết mờ, ngân sách, Haversine, WSM, feedback và lịch sử.'),
        ('AI/NLP', 'Giải thích Celery/Gemini có kiểm tra và fallback; phân tích câu tự nhiên; trợ lý RAG.'),
        ('Điểm đến/bản đồ', 'Lookup địa danh; trang chi tiết; thời tiết; tuyến Leaflet; kế hoạch nhiều điểm.'),
        ('Chỗ ở', 'Tìm gần theo PostGIS; loại phòng/tiện ích; đặt phòng; đánh giá sau checkout.'),
        ('Tour', 'Danh sách/chi tiết, điểm dừng, ngày khởi hành, kiểm tra slots và đặt tour.'),
        ('Thanh toán', 'VNPay và MoMo sandbox, callback/IPN, trạng thái đơn và refund.'),
        ('Cộng đồng/chat', 'Bài viết, lượt thích, hội thoại realtime và unread count.'),
        ('Quản trị', 'CRUD danh mục, tour, đơn, tiện ích, nội dung About và thống kê.'),
    ]
    add_table(doc, ['Module', 'Kết quả cài đặt'], module_rows, font_size=9)
    add_caption(doc, 'Bảng 3.2. Các module chính của hệ thống')

    add_heading(doc, '3.3. Kết quả kiểm thử', 2)
    add_note_box(doc, 'Không điền PASS hoặc số liệu giả. Chạy lệnh test trên đúng phiên bản nộp, lưu output và điền vào các ô [CẦN BỔ SUNG]. Ghi rõ test tự động không thay thế kiểm thử cổng sandbox/IPN public.')
    add_table(doc, ['Nhóm kiểm thử', 'Kịch bản cần chạy', 'Kết quả thực tế'], [
        ('Xác thực/phân quyền', 'Đăng ký, login/logout; quyền hồ sơ; truy cập route staff; quyền sở hữu đơn.', '[CẦN BỔ SUNG: số pass/fail]'),
        ('Gợi ý', 'Ngày ngoài cửa sổ, tiêu chí thiếu, sở thích liên quan/không liên quan, weather fallback, trọng số.', '[CẦN BỔ SUNG]'),
        ('Celery/AI', 'Task explanation thành công, lỗi Gemini, task status; task embedding và refresh cache.', '[CẦN BỔ SUNG]'),
        ('Đặt phòng/tour', 'Tồn kho, số chỗ, tính tiền server, hủy và refund preview.', '[CẦN BỔ SUNG]'),
        ('Đặt đồng thời', 'Nhiều thread cùng đặt tài nguyên cuối; xác nhận không vượt tồn kho.', '[CẦN BỔ SUNG: test cụ thể]'),
        ('Thanh toán', 'Mock callback chữ ký đúng/sai; sandbox VNPay/MoMo; idempotency.', '[CẦN BỔ SUNG]'),
        ('Chat', 'Websocket auth, phân quyền phòng, ping/pong, gửi realtime, unread/read.', '[CẦN BỔ SUNG]'),
        ('Frontend', 'npm test/build; responsive; luồng form và lỗi console.', '[CẦN BỔ SUNG]'),
    ], font_size=9)
    add_caption(doc, 'Bảng 3.3. Ma trận kiểm thử cần hoàn tất trên bản chốt')
    add_heading(doc, '3.3.1. Kết quả kiểm thử tự động', 3)
    add_paragraph(doc, 'Lệnh chạy, môi trường DB/Redis, thời gian và số test phải được ghi theo output thực tế. Báo cáo chính thức nên đính kèm log rút gọn hoặc ảnh chụp terminal ở phụ lục, không chỉ ghi “đã kiểm thử”.')
    add_paragraph(doc, 'Lệnh dự kiến: `docker compose exec backend python manage.py test --verbosity 2` và tại frontend `npm test` (nếu script test được cấu hình). Sau khi chạy, cập nhật: ngày chạy [___], tổng test backend [___], pass [___], fail/error [___], frontend [___], mã commit [___].')
    add_heading(doc, '3.3.2. Kiểm thử nghiệp vụ thủ công', 3)
    add_paragraph(doc, 'Ghi lại các bước từ đầu tới cuối: tìm gợi ý → mở chi tiết → lập kế hoạch → chọn phòng/tour → tạo đơn → thanh toán sandbox → quay về website → xem trạng thái trong hồ sơ → hủy đơn khi đủ điều kiện. Với IPN, phân biệt kết quả mô phỏng bằng test và lần gọi thực tế từ môi trường công khai.')

    add_heading(doc, '3.4. Đánh giá thuật toán và hiệu năng', 2)
    add_paragraph(doc, 'Chất lượng xếp hạng cần đánh giá theo bộ truy vấn, không chỉ một lần demo. README ghi lại một phép hiệu chỉnh ngưỡng sở thích trên 35 điểm đến đã embedding: truy vấn liên quan có cosine thấp nhất 0,425053 và nhóm không liên quan có cosine cao nhất 0,175904; cấu hình dùng ngưỡng PREFERENCE_MATCH_MIN=0,30. Bảng này là phép đo mẫu trên bộ dữ liệu và ngày đã nêu trong README, không phải đánh giá tổng quát trên người dùng hay toàn bộ điểm đến Việt Nam.')
    add_table(doc, ['Nhóm', 'Truy vấn mẫu', 'Cosine cao nhất'], [
        ('Liên quan', 'biển', '0,693640'),
        ('Liên quan', 'núi', '0,450897'),
        ('Liên quan', 'ẩm thực', '0,474012'),
        ('Liên quan', 'văn hóa lịch sử', '0,436829'),
        ('Liên quan', 'nghỉ dưỡng', '0,468392'),
        ('Liên quan', 'đi biển ăn hải sản', '0,425053'),
        ('Không liên quan', 'xyz', '0,175904'),
        ('Không liên quan', 'bóng đá', '0,096845'),
        ('Không liên quan', 'lập trình', '0,071849'),
        ('Không liên quan', 'asdfgh', '0,088793'),
    ], font_size=9)
    add_caption(doc, 'Bảng 3.4. Số liệu hiệu chỉnh ngưỡng từ README; xác nhận lại commit và tái chạy trước khi nộp')
    add_paragraph(doc, 'Đo thời gian phản hồi cần tách warm cache/cold cache, số lượng điểm đến, tình trạng Sentence-BERT đã nạp, kết nối dịch vụ ngoài và máy thử. Ghi tối thiểu số lần lặp, trung vị và p95. Không lấy thời gian một request đơn lẻ làm cam kết hiệu năng.')
    add_table(doc, ['Thử nghiệm', 'Số lần', 'Median (s)', 'P95 (s)', 'Ghi chú'], [
        ('Recommendation API, cache ấm', '[điền]', '[điền]', '[điền]', '[máy, số điểm, model]'),
        ('Recommendation API, cache lạnh', '[điền]', '[điền]', '[điền]', '[máy, số điểm, model]'),
        ('Task giải thích Gemini', '[điền]', '[điền]', '[điền]', '[model/API response]'),
    ], font_size=9)
    add_caption(doc, 'Bảng 3.5. Mẫu ghi nhận benchmark — số liệu hiện chưa được điền')

    add_heading(doc, '3.5. Nhận xét, hạn chế và rủi ro', 2)
    add_paragraph(doc, 'Ưu điểm của phương án là điểm xếp hạng có thể quan sát từng thành phần; tiêu chí vắng không bị gán điểm giả; dữ liệu thời tiết được cache thô để dùng lại; công việc LLM tách khỏi request; nghiệp vụ đặt và thanh toán có kiểm tra server; PostGIS đảm nhiệm lọc bán kính.')
    add_paragraph(doc, 'Hạn chế gồm dữ liệu chỗ ở/tour mang tính minh họa, số điểm đến chưa phủ mọi địa danh, dự báo chỉ tối đa 16 ngày, mô hình embedding pretrained phụ thuộc chất lượng mô tả, nguồn thời tiết/route/LLM phụ thuộc mạng và quota. Thanh toán chỉ là sandbox. Tunnel từ máy cá nhân không bảo đảm uptime. Chất lượng gợi ý chưa được đo bằng nghiên cứu người dùng quy mô lớn.')
    add_note_box(doc, 'Trước khi chốt: tái hiện và sửa lỗi trang kế hoạch khi thêm/chỉnh điểm thứ hai; rà contrast chữ trên bài cộng đồng; kiểm tra các luồng này sau build. Không đưa ảnh trang lỗi vào mục kết quả như một tính năng hoàn tất.')

    page_break(doc)
    add_heading(doc, 'KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN', 1)
    add_heading(doc, '1. Kết luận', 2)
    add_paragraph(doc, 'Đồ án đã thiết kế và xây dựng một website du lịch tích hợp các chức năng gợi ý đa tiêu chí, điểm đến, bản đồ, kế hoạch cá nhân, tour, chỗ ở, đặt dịch vụ, quản trị, cộng đồng, chat và trợ lý tri thức. Thuật toán gợi ý kết hợp embedding Sentence-BERT, logic mờ, chấm ngân sách, Haversine và WSM. Cấu trúc nhiều tầng giúp giao diện gọi API, backend kiểm tra nghiệp vụ và dữ liệu được lưu tập trung.')
    add_paragraph(doc, 'Mức độ hoàn thành cuối cùng phải được đối chiếu với kết quả kiểm thử đã chạy và lỗi còn tồn tại tại ngày nộp. Các nội dung tour/chỗ ở được xác định là demo; giao dịch sandbox không phải thanh toán thật. Những giới hạn này cần được nêu trong kết luận thay vì mô tả như dịch vụ thương mại đang vận hành.')
    add_heading(doc, '2. Kiến thức và kỹ năng tích lũy', 2)
    for text in [
        'Củng cố kiến thức về API, xác thực, phân quyền, transaction và thiết kế dữ liệu quan hệ.',
        'Vận dụng embedding ngữ nghĩa, cosine, fuzzy membership, WSM và Haversine vào bài toán gợi ý.',
        'Tích hợp PostgreSQL/PostGIS, Redis, Celery, WebSocket và dịch vụ API bên ngoài.',
        'Thiết kế quy trình thanh toán sandbox, xác minh callback và xử lý tình huống lỗi/fallback.',
        'Thực hành kiểm thử chức năng, quan sát log, đóng gói Docker và chuẩn bị demo.',
    ]:
        add_bullet(doc, text)
    add_heading(doc, '3. Hướng phát triển', 2)
    for text in [
        'Bổ sung nguồn dữ liệu điểm đến được xác minh và nâng chất lượng mô tả, ảnh, giá tham khảo.',
        'Đánh giá gợi ý bằng tập dữ liệu lớn hơn, khảo sát người dùng và các chỉ số Precision@K/NDCG.',
        'Cải thiện cache, monitoring, retry, rate limit và khả năng phục hồi dịch vụ ngoài.',
        'Triển khai trên hạ tầng ổn định có domain/HTTPS, backup, secrets management và logging.',
        'Hoàn thiện tích hợp callback/refund thực tế theo yêu cầu merchant sau khi có môi trường public phù hợp.',
        'Cải thiện lịch trình nhiều điểm, gợi ý thời lượng và tối ưu thứ tự tham quan khi có dữ liệu đáng tin cậy.',
    ]:
        add_bullet(doc, text)

    page_break(doc)
    add_heading(doc, 'PHỤ LỤC A. HƯỚNG DẪN CHẠY VÀ DEMO', 1)
    add_paragraph(doc, 'Các lệnh dưới đây là mẫu theo cấu hình Docker Compose trong repository. Cần kiểm tra README/.env.example hiện hành trước khi dùng; không đưa giá trị bí mật từ `.env` vào phụ lục.', first_line=True)
    add_paragraph(doc, '1. Khởi động các dịch vụ phát triển: `docker compose up -d db redis backend celery`.', first_line=False)
    add_paragraph(doc, '2. Khởi động frontend trong terminal riêng: `cd frontend` rồi `npm run dev`.', first_line=False)
    add_paragraph(doc, '3. Mở địa chỉ Vite được in ra terminal; đăng nhập tài khoản demo do admin tạo hoặc đăng ký tài khoản thử.', first_line=False)
    add_paragraph(doc, '4. Kiểm tra API/backend, task worker, dữ liệu và dịch vụ ngoài trước khi demo.', first_line=False)
    add_paragraph(doc, '5. Nếu dùng tunnel để truy cập từ mạng khác, xác nhận tunnel/hostname và backend allowed hosts, CSRF trusted origins, cookie settings phù hợp; chỉ chia sẻ URL public, không chia sẻ token tunnel.', first_line=False)
    add_heading(doc, 'PHỤ LỤC B. MINH CHỨNG CẦN BỔ SUNG', 1)
    for text in [
        'Ảnh 1: Trang chủ và trạng thái chưa đăng nhập.',
        'Ảnh 2: Form tiêu chí và vị trí xuất phát.',
        'Ảnh 3: Kết quả gợi ý có điểm thành phần và thời tiết.',
        'Ảnh 4: Trang chi tiết, route và danh sách chỗ ở theo bán kính.',
        'Ảnh 5: Đặt phòng/tour và số tiền trước thanh toán.',
        'Ảnh 6: Trang sandbox và kết quả callback.',
        'Ảnh 7: Chat hai chiều user/admin và unread count.',
        'Ảnh 8: Khu quản trị và dữ liệu demo.',
        'Log kiểm thử backend/frontend, mã commit, ngày chạy và cấu hình thử nghiệm.',
        'Kết quả benchmark từ script/lệnh thực tế, kèm thông tin cache và số điểm đến.',
    ]:
        add_bullet(doc, text)
    add_note_box(doc, 'Không chèn ảnh chứa email cá nhân, điện thoại, token, khóa API, mật khẩu hoặc dữ liệu người dùng thật.')

    page_break(doc)
    add_heading(doc, 'DANH MỤC TÀI LIỆU THAM KHẢO', 1)
    references = [
        '[1] J. Yoon and C. Choi, “Real-Time Context-Aware Recommendation System for Tourism,” Sensors, vol. 23, no. 7, Art. no. 3679, 2023.',
        '[2] K. Chrysafiadi, A. Kontogianni, M. Virvou, and E. Alepis, “Enhancing User Experience in Smart Tourism via Fuzzy Logic-Based Personalization,” Mathematics, vol. 13, no. 5, Art. no. 846, 2025.',
        '[3] N. Reimers and I. Gurevych, “Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks,” in Proc. EMNLP-IJCNLP, Hong Kong, 2019, pp. 3982–3992.',
        '[4] J. Lu, “Personalized Recommendation Algorithm of Smart Tourism Based on Cross-Media Big Data and Neural Network,” Computational Intelligence and Neuroscience, 2022, Art. no. 9566766.',
        '[5] Y. Rafique, J. Wu, A. W. Muzaffar, and B. Rafique, “An Enhanced Integrated Fuzzy Logic-Based Deep Learning Techniques for Recommendation System,” PeerJ Computer Science, vol. 10, 2024, Art. no. e2529.',
        '[6] N. L. U. Minh and N. M. Tâm, “Ứng dụng Trí tuệ Nhân tạo trong Du lịch,” Tạp chí Khoa học Trường Đại học Phan Thiết, vol. 2, no. 4, 2024.',
        '[7] Django Software Foundation, “Django documentation, version 5.2.” [Trực tuyến]. https://docs.djangoproject.com/en/5.2/. [Truy cập: 13/09/2026].',
        '[8] Django REST framework, “Django REST framework documentation.” [Trực tuyến]. https://www.django-rest-framework.org/. [Truy cập: 13/09/2026].',
        '[9] The PostgreSQL Global Development Group, “PostgreSQL documentation.” [Trực tuyến]. https://www.postgresql.org/docs/current/. [Truy cập: 13/09/2026].',
        '[10] Google, “Gemini API documentation: Models.” [Trực tuyến]. https://ai.google.dev/gemini-api/docs/models. [Truy cập: 13/09/2026].',
        '[11] Django Software Foundation, “GeoDjango documentation, version 5.2.” [Trực tuyến]. https://docs.djangoproject.com/en/5.2/ref/contrib/gis/. [Truy cập: 13/09/2026].',
        '[12] PostGIS Project, “ST_DWithin.” [Trực tuyến]. https://postgis.net/docs/ST_DWithin.html. [Truy cập: 13/09/2026].',
        '[13] V. Agafonkin and Leaflet contributors, “Leaflet API reference.” [Trực tuyến]. https://leafletjs.com/reference.html. [Truy cập: 13/09/2026].',
        '[14] P. Lewis et al., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” Advances in Neural Information Processing Systems, vol. 33, 2020.',
        '[15] Celery Project, “Celery documentation.” [Trực tuyến]. https://docs.celeryq.dev/. [Cần cập nhật ngày truy cập trước khi nộp].',
        '[16] Open-Meteo, “Weather Forecast API.” [Trực tuyến]. https://open-meteo.com/en/docs. [Cần cập nhật ngày truy cập trước khi nộp].',
        '[17] OpenStreetMap Wiki, “Nominatim.” [Trực tuyến]. https://wiki.openstreetmap.org/wiki/Nominatim. [Cần cập nhật ngày truy cập trước khi nộp].',
        '[18] OpenRouteService, “API documentation.” [Trực tuyến]. https://openrouteservice.org/dev/#/api-docs. [Cần cập nhật ngày truy cập trước khi nộp].',
        '[19] Redis Ltd., “Redis documentation.” [Trực tuyến]. https://redis.io/docs/latest/. [Cần cập nhật ngày truy cập trước khi nộp].',
        '[20] Django Channels, “Channels documentation.” [Trực tuyến]. https://channels.readthedocs.io/. [Cần cập nhật ngày truy cập trước khi nộp].',
    ]
    for ref in references:
        p = add_paragraph(doc, ref, first_line=False)
        p.paragraph_format.left_indent = Cm(0.7)
        p.paragraph_format.hanging_indent = Cm(0.7)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(4)

    # Ask Microsoft Word to refresh fields such as the table of contents on open.
    settings = doc.settings._element
    update_fields = OxmlElement('w:updateFields')
    update_fields.set(qn('w:val'), 'true')
    settings.append(update_fields)
    doc.core_properties.title = 'Xây dựng website đặt tour du lịch thông minh tích hợp AI'
    doc.core_properties.subject = 'Bản thảo báo cáo đồ án chuyên ngành Công nghệ phần mềm'
    doc.core_properties.author = 'Nguyễn Minh Tiến'
    doc.save(OUTPUT)
    print(f'Created {OUTPUT}')


if __name__ == '__main__':
    build()

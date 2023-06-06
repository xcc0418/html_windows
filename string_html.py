
def str_header_html3(name, asin):
    str_name_col = f'<td class="list_control1"><div class="list_control1"><span>{name}</span><span class="table-sort">' \
                     f'<i class="sort-asc" onclick="ascending_sort(event)" sort_name="{name}" sort_asin="{asin}"></i>' \
                     f'<i class="sort-desc" onclick="descending_sort(event)" sort_name="{name}" sort_asin="{asin}"></i></span></div></td>'
    return str_name_col


def str_header_html1():
    str_name_col = '<td class="list_control4"><div class="list_control4"><span>序号</span></div></td>' \
                   '<td class="list_control2"><div class="list_control2"><span>本地父体</span></div></td>' \
                   '<td class="list_control3"><div class="list_control3"><span>本地品名</span></div></td>'
    return str_name_col


def str_header_html2():
    str_name_col = '<td class="list_control2"><div class="list_control2"><span>亚马逊父体</span></div></td>' \
                   '<td class="list_control3"><div class="list_control3"><span>本地品名</span></div></td>'
    return str_name_col


def str_content_html(content, control_class):
    str_name_col = f'<td class="{control_class}"><div class="{control_class}"><span>{content}</span></div></td>'
    return str_name_col


def str_content_name(content, asin):
    str_name_col = f'<td class="list_control3"><div class="list_control3"><span ondblclick="windows_msg(event)" class="{asin}" oncontextmenu="menu_bar(event)" onclick="close_menu()">{content}</span></div></td>'
    return str_name_col

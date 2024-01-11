from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.generic import ListView
from bs4 import BeautifulSoup
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from .models import Product
import requests
from io import BytesIO
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from django.http import HttpResponse
import datetime


def home(request):
    context = {
        'products': []
    }
    if 'products' not in request.session:
        request.session['products'] = []

    if 'code' in request.GET:
        code = request.GET['code'].strip()
        codes = code.split(' ')
        for code in codes:
            if len(code) > 3:
                existing_product = next((item for item in request.session['products'] if item['code'] == code), None)
                if existing_product:
                    messages.success(request, 'Артикуль уже добавлен!')
                    return redirect('home')
                try:
                    product = Product.objects.get(code__iexact=code.strip())
                    title = product.info + ' / ' + product.code
                    img_src = f'/products/{product.image}'
                    new_product = {'code': code, 'title': title, 'img_src': img_src,
                                'price': product.price, 'quantity': 1, 'org_articul': product.code, 'brand': product.brand}
                    request.session['products'].append(new_product)
                    request.session.modified = True
                except:
                    try:
                        title, img_src, price, org_articul, web, brand = get_data(code)
                        existing_product = next((item for item in request.session['products'] if item['code'] == code), None)
                        new_product = {'code': code, 'title': title, 'img_src': img_src,
                                        'price': price, 'quantity': 1, 'org_articul': org_articul, 'web': web, 'brand': brand}
                        request.session['products'].append(new_product)
                        request.session.modified = True

                    except:
                        try:
                            title, img_src, price, org_articul, web, brand = get_fenix(code)
                            fenix_web = 'https://favourite-light.com'
                            new_product = {'code': code, 'title': title, 'img_src': f"{fenix_web}{img_src}",
                                        'price': price, 'quantity': 1, 'org_articul': org_articul, 'web': web, 'brand': brand}
                            request.session['products'].append(new_product)
                            request.session.modified = True
                        except Exception as e:
                            print(e)

    total_sum = 0
    for product in request.session.get('products', []):
        total_sum += int(product['price']) * int(product['quantity'])
    context['total_sum'] = total_sum
    context['products'] = request.session['products']

    lms_products = Product.objects.all()
    context['lms_products'] = lms_products
    return render(request, 'main.html', context)

def clear_session(request):
    user_id = request.session.get('_auth_user_id')
    backend_path = request.session.get('_auth_user_backend')
    session_key = request.session.get('_auth_user_hash')
    request.session.clear()
    if user_id and backend_path and session_key:
        request.session['_auth_user_id'] = user_id
        request.session['_auth_user_backend'] = backend_path
        request.session['_auth_user_hash'] = session_key

    return redirect('home')


@require_http_methods(["GET"])
def update_quantity(request):
    try:
        code = request.GET.get('code')
        change = int(request.GET.get('change', 0))

        if 'products' in request.session:
            # Find the product with the matching code
            existing_product = next((item for item in request.session['products'] if item['code'] == code), None)
            if existing_product:
                # new_quantity = max(existing_product['quantity'] + change, 0)
                new_quantity = max(change, 0)
                existing_product['quantity'] = new_quantity
                request.session.modified = True
                return JsonResponse({'status': 'success', 'message': 'Quantity updated successfully'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': 'No products in session'}, status=404)

    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)
    except Exception as e:
        # Handle other exceptions
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(["GET"])
def delete_product(request):
    code = request.GET.get('code')

    if 'products' in request.session:
        request.session['products'] = [item for item in request.session['products'] if item['code'] != code]
        request.session.modified = True

        return JsonResponse({'status': 'success', 'message': 'Product deleted successfully'})

    return JsonResponse({'status': 'error', 'message': 'No products in session'}, status=404)


@require_http_methods(["POST"])
def add_to_cart(request):
    code = request.POST.get('code')
    title = request.POST.get('title')
    img_src = f"{request.POST.get('img_src')}"
    price = request.POST.get('price')
    org_articul = request.POST.get('org_articul')
    brand = request.POST.get('brand')
    new_product = {
        'code': code,
        'title': title,
        'img_src': img_src,
        'price': price,
        'quantity': 1,
        'org_articul': org_articul,
        'brand': brand,
    }

    # Add product to session
    existing_product = next((item for item in request.session['products'] if item['code'] == code), None)
    if existing_product:
        messages.success(request, 'Артикуль уже добавлен!')
        return JsonResponse({'status': 'success'})
    request.session['products'].append(new_product)
    request.session.modified = True
    return JsonResponse({'status': 'success'})


def download_excel(request):
    products = request.session.get('products', [])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    t_date = datetime.date.today().strftime("%d-%m")
    f_name = f'products_{t_date}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{f_name}"'

    workbook = Workbook()
    sheet = workbook.active
    sheet.column_dimensions['A'].width = 6
    sheet.column_dimensions['B'].width = 20
    sheet.column_dimensions['C'].width = 14
    sheet.column_dimensions['D'].width = 40
    sheet.column_dimensions['E'].width = 6
    sheet.column_dimensions['F'].width = 10
    sheet.column_dimensions['G'].width = 10

    # Define your column names here
    column_names = ["#", "Фото", "Артикул", "Описание", "Кол-во", "Цена", "Сумма", "Бренд"]

    # Set the column names in the first row
    for col_num, column_title in enumerate(column_names, start=1):
        sheet.cell(row=1, column=col_num, value=column_title)

    for row_num, product in enumerate(products, start=2):
        sheet[f'A{row_num}'] = row_num
        sheet[f'C{row_num}'] = product['org_articul']
        sheet[f'D{row_num}'] = product['title']
        sheet[f'E{row_num}'] = int(product['quantity'])
        sheet[f'F{row_num}'] = int(product['price'])
        sheet[f'G{row_num}'] = int(product['price']) * int(product['quantity'])
        sheet[f'H{row_num}'] = product['brand']

        web_base = product.get('img_src')[:5]
        web_src = product.get('img_src')
        if 'http' not in web_base:
            host = request.get_host()
            web_src = f"http://{host}{product.get('img_src')}"
        if product.get('img_src'):
            image_response = requests.get(web_src)
            if image_response.status_code == 200:
                image = Image(BytesIO(image_response.content))
                desired_width = 140  # Set your desired width
                aspect_ratio = image.width / image.height
                image.width = desired_width
                image.height = desired_width / aspect_ratio
                sheet.add_image(image, f'B{row_num}')
                points_height = image.height * (75 / 96)  # Convert pixels to points
                sheet.row_dimensions[row_num].height = points_height

    workbook.save(response)
    return response


def get_data(articul):
    baseweb = 'https://maytoni.ru'
    web_link = f'https://maytoni.ru/search/?q={articul}'
    source = requests.get(web_link).text
    soup = BeautifulSoup(source, 'lxml')
    try:
        org_articul = soup.find('div', class_='catalog-card__article __js-copy-article').span.text.replace('Артикул: ', '')
    except Exception as e:
        print('website error:', e)
        org_articul = articul

    p_link = soup.find('a', class_='catalog-card__link')['href']
    pf_link = f'https://maytoni.ru{p_link}'
    source2 = requests.get(pf_link).text
    soup2 = BeautifulSoup(source2, 'lxml')

    product_desc_div = soup2.find('div', class_='product-card__properties')
    size = product_desc_div.get_text(separator=' ', strip=True)
    product_desc_div2 = soup2.find_all('div', class_='product-card__desc-item')

    features = f'{size}'
    for pro in product_desc_div2:
        ftr = pro.get_text(separator=' ', strip=True).split(' ')
        ftr_txt = ' '.join([i for i in ftr if i]).replace(',', '').replace('Количество', 'Кол-во')
        if 'Цветовая' in ftr_txt or 'Мощность' in ftr_txt or 'Степень защиты' in ftr_txt:
            features += ', ' + ftr_txt.replace('Цветовая температура', '').replace('Мощность', '').replace('Степень защиты', '')
        else:
            features += '<br>' + ftr_txt
    features = features.replace('Высота', "Выс.").replace('Ширина', "Шир.").replace('Диаметр', "Диам.").replace('Длина', "Дл.")
    title = soup.find('div', class_='catalog-card__title').text.strip() + '<br>' + features
    title = mark_safe(title)
    price = [i for i in soup.find('span', class_='price').text if i.isdigit()]
    d_price = int(''.join(price))
    s_price = round(d_price*1.1, -1)
    img_src = soup.find('picture', class_='catalog-card__img-img active').find('img')['src']
    img_src = f'{baseweb}{img_src}'
    brand = 'Maytoni'
    return title, img_src, s_price, org_articul, pf_link, brand


def get_fenix(articul):
    # art = 'https://favourite-light.com/catalog/?s=1002-TB-300'
    web_link = f'https://favourite-light.com/catalog/?s={articul}'
    source = requests.get(web_link).text
    soup = BeautifulSoup(source, 'lxml')
    img_src = soup.find('div', class_='sb_block_img').find('img')['src']
    link2 = soup.find('a', class_="b-product__wrap-link")['href']
    web2 = f'https://favourite-light.com{link2}'
    source2 = requests.get(web2).text
    soup2 = BeautifulSoup(source2, 'lxml')
    price = [i for i in soup2.find('span', class_='sb_price').text if i.isdigit()]
    price = int(''.join(price))
    ftrs_divs = soup2.find_all('div', 'catalog-item__data')
    check_list = ["длина", "ширина", "высота", "диаметр", "материал", "отделка", "цоколь"]
    articul2 = ''
    ftrs = ''
    for ftr in ftrs_divs:
        txt = ftr.text.replace('\n', ' ').strip().lower()
        if 'артикул' in txt:
            articul2 = txt.replace('артикул ', "")
        if any(check_item in txt for check_item in check_list):
            ftrs += txt + ', '
    idx1 = ftrs.find('цвет, отделка')
    title = ftrs.replace('цвет, отделка ', '')
    t1 = title[idx1:]
    title = t1 + title[:idx1]
    title = title.replace('высота', 'выс.').replace('длина', 'дл.').replace('ширина', 'шир.').replace('материал', '')
    s_price = round(price * 1.25, -1)
    org_articul = articul2.upper()
    assert articul == org_articul
    brand = 'Favourite'
    return title.title(), img_src, s_price, org_articul, web2, brand
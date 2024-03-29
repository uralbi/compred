from django.shortcuts import render, redirect
from django.core.cache import cache
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.generic import ListView
from bs4 import BeautifulSoup
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils.safestring import mark_safe
from .models import Product, Promotions, Margin
import requests
from PIL import Image as PILImage
from io import BytesIO
from openpyxl import Workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from django.http import HttpResponse
import datetime
import re


def may_products(request):
    cache_time = 86400
    ctx = {
        'mtps': [],
        'track': [],
        'spots': [],
    }
    if 'mtps' not in request.session:
        request.session['mtps'] = []
    if 'track' not in request.session:
        request.session['track'] = []
    if 'spots' not in request.session:
        request.session['spots'] = []

    cached_data = cache.get('maytoni_led')
    cached_tracks = cache.get('maytoni_track')
    cached_spots = cache.get('maytoni_spots')
    if cached_data is not None:
        parsed_data = cached_data
    else:
        parsed_data = get_may_products(request)
        cache.set('maytoni_led', parsed_data, timeout=cache_time)
    for new_product in parsed_data:
        request.session['mtps'].append(new_product)

    if cached_tracks is not None:
        parsed_tracks = cached_tracks
    else:
        parsed_tracks = get_may_tracks(request)
        cache.set('maytoni_track', parsed_tracks, timeout=cache_time+3600)
    for new_track in parsed_tracks:
        request.session['track'].append(new_track)

    if cached_spots is not None:
        parsed_spots = cached_spots
    else:
        parsed_spots = get_may_spots(request)
        cache.set('maytoni_spots', parsed_spots, timeout=cache_time+3600*2)
    for new_spot in parsed_spots:
        request.session['spots'].append(new_spot)

    request.session.modified = True

    ctx['mtps'] = request.session['mtps']
    ctx['track'] = request.session['track']
    ctx['spots'] = request.session['spots']
    return render(request, 'mtps.html', ctx)

def showroom(request):
    ctx = {
        'products': []
    }
    ctx['products'] = Product.objects.all()
    return render(request, 'products.html', ctx)

# def homepage(request):
#     context = {
#         'products': []
#     }
#     proms = Promotions.objects.all()
#     products = [prom.product for prom in proms if prom.product]
#     context['products'] = products
#     return render(request, 'index.html', context)

def home(request):
    context = {
        'products': []
    }
    if 'products' not in request.session:
        request.session['products'] = []
    lms_products = Product.objects.select_related('brand').all()
    if 'code' in request.GET:
        code = request.GET['code'].strip()
        codes = code.split(';')
        margin = Margin.objects.all()
        for code in codes:
            if len(code) > 3:
                existing_product = next((item for item in request.session['products'] if item['code'] == code), None)
                if existing_product:
                    messages.success(request, 'Артикул уже добавлен!')
                    return redirect('home')
                try:
                    product = lms_products.get(code__iexact=code.strip())
                    title = product.info + ' / ' + product.code
                    img_src = f'/products/{product.image}'
                    new_product = {'code': code, 'title': title.replace('\n', ' '), 'img_src': img_src,
                                'price': product.price, 'quantity': 1, 'org_articul': product.code, 'brand': product.brand.name}
                    print('new product:', new_product)
                    request.session['products'].append(new_product)
                    request.session.modified = True
                except Exception as e:
                    print(e)
                    if e:
                        try:
                            title, img_src, price, org_articul, web, brand = get_data(code)
                            mrg = margin.get(brand__name=brand).margin
                            existing_product = next((item for item in request.session['products'] if item['code'] == code), None)
                            price = int(round(price*(1+mrg/100), -1))
                            new_product = {'code': code, 'title': title, 'img_src': img_src,
                                            'price': price, 'quantity': 1, 'org_articul': org_articul, 'web': web, 'brand': brand}
                            request.session['products'].append(new_product)
                            request.session.modified = True
                        except Exception as e:
                            try:
                                title, img_src, price, org_articul, web, brand = get_fenix(code)
                                mrg = margin.get(brand__name=brand).margin
                                price = int(round(price*(1+mrg/100), -1))
                                fenix_web = 'https://favourite-light.com'
                                new_product = {'code': code, 'title': title, 'img_src': f"{fenix_web}{img_src}",
                                            'price': price, 'quantity': 1, 'org_articul': org_articul, 'web': web, 'brand': brand}
                                request.session['products'].append(new_product)
                                request.session.modified = True
                            except Exception as e:
                                try:
                                    title, img_src, price, org_articul, web, brand = get_vamsvet(code)
                                    mrg = margin.get(brand__name=brand).margin
                                    price = int(round(price*(1+mrg/100), -1))
                                    new_product = {'code': code, 'title': title, 'img_src': f"{img_src}",
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
        change = float(request.GET.get('change', 0))
        price = float(request.GET.get('price', 0))

        if 'products' in request.session:
            existing_product = next((item for item in request.session['products'] if item['code'] == code), None)

            if existing_product:
                new_quantity = max(change, 0)
                existing_product['quantity'] = new_quantity
                existing_product['price'] = price
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
    code = request.POST.get('code').replace(' ', '-')
    print('add to cart:', code)
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
        messages.success(request, 'Артикул уже добавлен!')
        return JsonResponse({'status': 'success'})
    request.session['products'].append(new_product)
    request.session.modified = True
    return JsonResponse({'status': 'success'})

def download_excel(request):
    products = request.session.get('products', [])
    num_of_pds= len(products)
    if num_of_pds == 0:
        return HttpResponse("No data", status=204)
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
                png_image = fetch_image_and_convert_to_png(web_src)
                desired_width = 140                                 # Set your desired width
                aspect_ratio = png_image.width / png_image.height
                new_height = int(desired_width / aspect_ratio)
                points_height = new_height * (75 / 96)              # Convert pixels to points
                png_image = resize_image_to_fit_row_height(png_image, new_height-4 )
                image_buffer = BytesIO()
                png_image.save(image_buffer, format='PNG')
                image_buffer.seek(0)
                openpyxl_image = OpenpyxlImage(image_buffer)
                sheet.add_image(openpyxl_image, f'B{row_num}')
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
    img_src = soup.find('picture', class_='catalog-card__img-img active').find('img')['src']
    img_src = f'{baseweb}{img_src}'
    brand = 'Maytoni'
    return title, img_src, d_price, org_articul, pf_link, brand

def get_fenix(articul):
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
    org_articul = articul2.upper()
    assert articul == org_articul
    brand = 'Fenix'
    return title.title(), img_src, price, org_articul, web2, brand

def get_vamsvet(articul):
    # art = 'https://www.vamsvet.ru/search/?q=FR6005CL-L48G'
    web_link = f'https://www.vamsvet.ru/search/?q={articul}'
    webbase = 'https://www.vamsvet.ru'
    source = requests.get(web_link).text
    soup = BeautifulSoup(source, 'lxml')

    link2 = soup.find('div', class_='prod__img-wrap').find('a')['href']

    img_src = f"{webbase}{soup.find('img', class_='prod__img')['src']}"
    price = [i for i in soup.find('div', class_='prod__price-cur').text if i.isdigit()]
    price = int(''.join(price))

    web2 = f'{webbase}{link2}'
    source2 = requests.get(web2).text
    soup2 = BeautifulSoup(source2, 'lxml')
    title = soup2.find('h1', class_="page-title").text.strip()
    org_articul = soup2.find('div', class_='prod-tec__value').text.strip()

    tec_divs = soup2.find_all('div', class_="prod-tec__car")
    ftr = ''
    selected_ftr = ('Коллекция', "Высота, мм", "Диаметр, мм", "Ширина, мм", "Вес,", "Мощность лампы,", "Цветовая", "Глубина, мм",
                    'Длина, мм', "Тип цоколя")
    for div in tec_divs:
        ftr_name = ' '.join(div.find('div', class_='prod-tec__name').text.strip().split(' ')[:2])
        ftr_val = div.find('div', class_='prod-tec__value').text.strip().split(' ')[0]
        ftr_name = re.sub(r'\s+', ' ', ftr_name).strip()
        ftr_val = re.sub(r'\s+', ' ', ftr_val).strip()
        if ftr_name in selected_ftr:
            ftr += ftr_name +': '+ ftr_val + ', '
    brand = 'Vamsvet'
    title = title.title() + " " + ftr
    return title, img_src, price, org_articul, web2, brand

def logout_view(request):
    logout(request)
    return redirect('home')

def get_may_products(request):
    baseweb = 'https://maytoni.ru'
    parsed_data=[]
    products = div_parser('https://maytoni.ru/search/?q=светодиодная лента', 'catalog__item')
    mrg = Margin.objects.get(brand__name='Maytoni').margin
    for product in products:
        image_src = product.find("picture", class_="catalog-card__img-img active").find('img')['src']
        articul = product.find("div", class_="catalog-card__article").text.strip().split(":")[1].strip()
        title = product.find("div", class_="catalog-card__title").text.strip()
        try:
            price = product.find("span", class_="price").text.strip()
            price = int(''.join([i for i in price if i.isdigit()]))
            price = int(round(price*(1+mrg/100), -1))
        except:
            continue
        new_product = {'image': f'{baseweb}{image_src}', 'articul': articul, 'title': title, 'price': price,}
        parsed_data.append(new_product)
    return parsed_data

def get_may_tracks(request):
    baseweb = 'https://maytoni.ru'
    parsed_data=[]
    products = div_parser('https://maytoni.ru/search/?q=шинопровод', 'catalog__item')
    mrg = Margin.objects.get(brand__name='Maytoni').margin
    for product in products:
        image_src = product.find("picture", class_="catalog-card__img-img active").find('img')['src']
        articul = product.find("div", class_="catalog-card__article").text.strip().split(":")[1].strip()
        title = product.find("div", class_="catalog-card__title").text.strip()
        try:
            price = product.find("span", class_="price").text.strip()
            price = int(''.join([i for i in price if i.isdigit()]))
            price = int(round(price*(1+mrg/100), -1))
        except:
            continue
        new_product = {'image': f'{baseweb}{image_src}', 'articul': articul, 'title': title, 'price': price,}
        parsed_data.append(new_product)
    return parsed_data

def get_may_spots(request):
    baseweb = 'https://maytoni.ru'
    parsed_data=[]
    products = div_parser('https://maytoni.ru/search/?q=трековый светильник', 'catalog__item')
    mrg = Margin.objects.get(brand__name='Maytoni').margin
    for product in products:
        try:
            price = product.find("span", class_="price").text.strip()
            price = int(''.join([i for i in price if i.isdigit()]))
            price = int(round(price*(1+mrg/100), -1))
        except:
            continue
        image_src = product.find("picture", class_="catalog-card__img-img active").find('img')['src']
        articul = product.find("div", class_="catalog-card").find('a')['href'].split('/')[-2]
        title = product.find("div", class_="catalog-card__title").text.strip()
        new_product = {'image': f'{baseweb}{image_src}', 'articul': articul, 'title': title, 'price': price}
        parsed_data.append(new_product)
    return parsed_data

def div_parser(webl, class_name):
    source = requests.get(webl).text
    soup = BeautifulSoup(source, 'lxml')
    products = soup.find_all("div", class_=class_name)
    return products

def fetch_image(url):
    """Fetch an image from a URL and return it as a PIL image."""
    response = requests.get(url)
    if response.status_code == 200:
        return PILImage.open(BytesIO(response.content))
    else:
        response.raise_for_status()

def resize_image(pil_image, desired_width):
    """Resize PIL image to a desired width while maintaining aspect ratio."""
    aspect_ratio = pil_image.width / pil_image.height
    new_height = int(desired_width / aspect_ratio)
    return pil_image.resize((desired_width, new_height), PILImage.ANTIALIAS)

def add_image_to_sheet(sheet, pil_image, position, row_num):
    """Add a PIL image to an Excel sheet at the specified position."""
    with BytesIO() as image_io:
        pil_image.save(image_io, format='PNG')
        image_io.seek(0)
        openpyxl_image = OpenpyxlImage(image_io)
        sheet.add_image(openpyxl_image, position)

    # Set row height based on image height, converting pixels to points
    points_height = pil_image.height * (75 / 96)  # Convert pixels to points
    sheet.row_dimensions[row_num].height = points_height

def process_product_image(sheet, product, row_num):
    """Process and add product image to sheet."""
    img_src = product.get('img_src')
    if img_src:
        try:
            pil_image = fetch_image(img_src)
            resized_image = resize_image(pil_image, desired_width=140)  # Set your desired width here
            add_image_to_sheet(sheet, resized_image, f'B{row_num}', row_num)
        except Exception as e:
            print(f"Error processing image for product {product.get('code', 'Unknown')}: {e}")

def fetch_image_and_convert_to_png(url):
    response = requests.get(url)
    if response.status_code == 200:
        image = PILImage.open(BytesIO(response.content))
        png_image = image.convert("RGBA")
        return png_image
    else:
        response.raise_for_status()


def resize_image_to_fit_row_height(img, desired_height_pixels):
    original_width, original_height = img.size
    aspect_ratio = original_width / original_height
    new_height = desired_height_pixels
    new_width = int(new_height * aspect_ratio)
    resized_img = img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
    return resized_img
import gradio as gr
import mimetypes
import base64

# 工具函数：本地文件转data url
def file_to_data_url(filepath):
    if not filepath:
        return ""
    mime, _ = mimetypes.guess_type(filepath)
    if not mime:
        mime = "image/jpeg"
    with open(filepath, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f"data:{mime};base64,{b64}"

# 渲染单个产品卡片
def render_product_card(product, idx):
    img_url = product.get('image_url', '')
    # 判断是否为本地文件路径（不是http/https开头且不是data url）
    if img_url and not (img_url.startswith('http') or img_url.startswith('data:')):
        try:
            img_url = file_to_data_url(img_url)
        except Exception:
            img_url = ''
    card_html = f'''
    <div class="product-card" id="product-card-{idx}">
        <img src="{img_url}" class="product-img"/>
        <div class="product-title">{product.get('name', '')}</div>
        <div class="product-category">{product.get('category', '')}</div>
        <ul class="product-info">
            <li><b>品牌：</b>{product.get('brand', '')}</li>
            <li><b>成分：</b>{product.get('ingredients', '')}</li>
            <li><b>功效：</b>{product.get('effects', '')}</li>
            <li><b>备注：</b>{product.get('description', '')}</li>
        </ul>
    </div>
    '''
    return card_html

# 渲染所有产品卡片
def render_products_collection(products):
    if not products:
        return '<div style="color:#888;text-align:center;padding:32px;">暂无产品，请先添加。</div>'
    cards = [render_product_card(prod, idx) for idx, prod in enumerate(products)]
    html = f'''<div class="product-collection">{''.join(cards)}</div>'''
    return html

# 删除产品回调
def delete_product(idx, state):
    products = state['products']
    if idx is not None and idx != "" and len(products) > 0:
        idx = int(idx)
        if 0 <= idx < len(products):
            products.pop(idx)
    state['products'] = products
    # 更新下拉选项
    choices = [(p['name'], i) for i, p in enumerate(products)]
    return state, render_products_collection(products), gr.update(choices=choices, value=None), gr.Info('产品已删除！')

# 添加产品回调
def add_product(image, name, category, brand, ingredients, effects, description, state):
    image_url = ""
    if isinstance(image, str):
        image_url = image
    elif image is not None:
        image_url = image
    new_product = {
        'image_url': image_url,
        'name': name,
        'category': category,
        'brand': brand,
        'ingredients': ingredients,
        'effects': effects,
        'description': description
    }
    products = state['products']
    products.append(new_product)
    state['products'] = products
    # 更新下拉选项
    choices = [(p['name'], i) for i, p in enumerate(products)]
    # 清空输入并返回提示
    return (state, render_products_collection(products), None, "", "", "", "", "", "", gr.update(choices=choices, value=None), gr.Info('产品已添加！'))

def render_products_tab(app_state):
    products = app_state.value['products'] if hasattr(app_state, 'value') else app_state['products']
    with gr.Column():
        with gr.Accordion("💄 这里收藏了你的美妆产品：", open=False):
            gr.Markdown("""
            * 在聊天时询问或请求推荐产品，Mira 会询问是否添加为产品卡片
            * 也可以在这里手动管理产品
                        
            💡 Mira 会根据你的产品给出更好的建议哦~
            """, elem_classes="compact-markdown")
        gr.Markdown("#### 💄 产品卡片集")
        products_html = gr.HTML(value=render_products_collection(products), elem_id="products-html")
        
        # 添加产品模块
        gr.Markdown("#### ➕ 添加新产品")
        with gr.Row():
            with gr.Column(scale=1):
                image = gr.Image(label="产品图片", type="filepath")
            with gr.Column(scale=3):
                with gr.Row():
                    name = gr.Textbox(label="产品名称")
                    category = gr.Textbox(label="产品分类")
                    brand = gr.Textbox(label="品牌")  
                with gr.Row():
                    ingredients = gr.Textbox(label="成分")
                    effects = gr.Textbox(label="功效")
                    description = gr.Textbox(label="备注")
                add_btn = gr.Button("添加")
        # 删除产品模块
        gr.Markdown("#### ➖ 删除产品")
        with gr.Row():
            del_choices = [(p['name'], i) for i, p in enumerate(products)]
            del_idx = gr.Dropdown(choices=del_choices, label="选择要删除的产品", value=None)
            del_btn = gr.Button("删除所选产品")
        # 删除按钮绑定
        del_btn.click(delete_product, inputs=[del_idx, app_state], outputs=[app_state, products_html, del_idx, gr.Markdown(visible=False)])
        # 添加按钮绑定
        add_btn.click(
            add_product,
            inputs=[image, name, category, brand, ingredients, effects, description, app_state],
            outputs=[app_state, products_html, image, name, category, brand, ingredients, effects, description, del_idx, gr.Markdown(visible=False)]
        )
    # 返回产品 HTML 控件对象和 Dropdown 控件对象
    return [products_html, del_idx]

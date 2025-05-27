custom_css = '''
.gradio-container {background: #f8f9fa;}
.title {font-size:2.2em;font-weight:bold;color:#d63384;margin-bottom:0.2em;}
.subtitle{color:#868e96;}
#feedback-md {
    height: 400px;
    max-height: 400px;
    min-height: 250px;
    width: 100%;
    overflow: auto;
    background: #fff;
    border: 1px solid #eee;
    border-radius: 8px;
    padding: 12px;
    box-sizing: border-box;
}
.product-collection {
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    justify-content: flex-start;
}
.product-card {
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    width: 260px;
    padding: 16px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 16px;
    position: relative;
}
.product-img {
    width: 180px;
    height: 180px;
    object-fit: cover;
    border-radius: 8px;
    margin-bottom: 12px;
}
.product-title {
    font-size: 1.2em;
    font-weight: bold;
    margin-bottom: 4px;
    text-align: center;
}
.product-category {
    font-size: 1em;
    color: #d63384;
    margin-bottom: 8px;
    text-align: center;
}
.product-info {
    list-style: none;
    padding: 0;
    margin: 0 0 12px 0;
    width: 100%;
}
.product-info li {
    font-size: 0.98em;
    margin-bottom: 4px;
    text-align: left;
}
.delete-btn {
    background: #ff6b6b;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    cursor: pointer;
    font-size: 0.95em;
    position: absolute;
    right: 12px;
    top: 12px;
    transition: background 0.2s;
}
.delete-btn:hover {
    background: #d63384;
}
''' 
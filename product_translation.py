import urllib.parse
import html
import translators as ts
import re
import time
import streamlit as st


def translate_korean_to_english(korean_name, show_progress=True):
    """
    将韩语产品名称翻译为英语
    优先使用在线翻译引擎，手动翻译作为备用方案
    """
    if show_progress:
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("🔍 开始翻译...")
    
    # 优先尝试多个在线翻译服务（按优先级排序）
    translators = [
        ('bing', 'Bing翻译'),
        ('google', '谷歌翻译')
    ]
    
    for i, (translator_name, translator_display) in enumerate(translators):
        try:
            if show_progress:
                progress = int((i + 1) / len(translators) * 70) + 10  # 10-80%
                progress_bar.progress(progress)
                status_text.text(f"🌐 优先使用{translator_display}...")
                time.sleep(0.3)  # 让用户看到进度
            
            print(f"尝试{translator_display}: {korean_name}")
            english_name = ts.translate_text(
                korean_name,
                from_language='ko',
                to_language='en',
                translator=translator_name,
            )
            
            if show_progress:
                progress_bar.progress(100)
                status_text.text(f"✅ {translator_display}成功")
                time.sleep(1)  # 显示成功状态
                progress_bar.empty()
                status_text.empty()
            
            print(f"{translator_display}成功: {korean_name} -> {english_name}")
            return english_name
            
        except Exception as e:
            print(f"{translator_display}失败: {e}")
            continue
    
    # 所有在线翻译都失败，使用增强的手动翻译作为备用方案
    if show_progress:
        progress_bar.progress(85)
        status_text.text("📚 在线翻译失败，尝试手动翻译备用方案...")
        time.sleep(0.5)
    
    enhanced_fallback = enhanced_manual_translation(korean_name)
    
    if show_progress:
        progress_bar.progress(100)
        status_text.text("✅ 手动翻译备用方案完成")
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
    
    print(f"使用手动翻译备用方案: {korean_name} -> {enhanced_fallback}")
    return enhanced_fallback


def manual_translation_fallback(korean_name):
    """
    手动翻译备用方案（基于常见Lululemon产品关键词映射）
    """
    translation_map = {
        # 产品类型
        '소프트': 'Soft',
        '저지': 'Jersey',
        '클래식': 'Classic',
        '팬츠': 'Pants',
        '셔츠': 'Shirt',
        '후디': 'Hoodie',
        '조거': 'Jogger',
        '스웨트': 'Sweat',
        '크루': 'Crew',
        '탱크': 'Tank',
        '티셔츠': 'T-Shirt',
        '재킷': 'Jacket',
        '풀오버': 'Pullover',
        '스테디': 'Steady',
        '스테이트': 'State',
        '트레이닝': 'Training',
        '러닝': 'Running',
        '요가': 'Yoga',
        '워크아웃': 'Workout',
        '스포츠': 'Sports',
        '액티브': 'Active',
        '피트니스': 'Fitness',
        
        # 性别
        '맨': "Men's",
        '우먼': "Women's",
        '남성': "Men's",
        '여성': "Women's",
        
        # 材质/特性
        '스트레치': 'Stretch',
        '컴포트': 'Comfort',
        '라이트': 'Light',
        '헤비': 'Heavy',
        '프리미엄': 'Premium',
        '베이직': 'Basic',
        '에센셜': 'Essential',
        '코어': 'Core',
        '레귤러': 'Regular',
        '슬림': 'Slim',
        '와이드': 'Wide',
        '타이트': 'Tight',
        '루즈': 'Loose',
        '오버사이즈': 'Oversized',
        
        # 颜色相关
        '블랙': 'Black',
        '화이트': 'White',
        '그레이': 'Gray',
        '네이비': 'Navy',
        '레드': 'Red',
        '블루': 'Blue',
        '그린': 'Green',
        '옐로우': 'Yellow',
        '핑크': 'Pink',
        '퍼플': 'Purple',
        '오렌지': 'Orange',
        '브라운': 'Brown',
        '베이지': 'Beige',
        '크림': 'Cream',
        '아이보리': 'Ivory',
        
        # 尺码相关
        '엑스트라': 'Extra',
        '스몰': 'Small',
        '미디엄': 'Medium',
        '라지': 'Large',
        '엑스트라라지': 'Extra Large',
        
        # 其他常见词汇
        '프로': 'Pro',
        '플러스': 'Plus',
        '맥스': 'Max',
        '미니': 'Mini',
        '롱': 'Long',
        '숏': 'Short',
        '미드': 'Mid',
        '하이': 'High',
        '로우': 'Low',
        '노': 'No',
        '제로': 'Zero',
        '원': 'One',
        '투': 'Two',
        '쓰리': 'Three',
        '포': 'Four',
        '파이브': 'Five',
        
        # 新增缺失的词汇
        '핏': 'Fit',
        '롱슬리브': 'Long Sleeve',
        '쇼츠': 'Shorts',
        '숏슬리브': 'Short Sleeve',
        '슬리브': 'Sleeve',
        '레귤러': 'Regular',
        '아시아': 'Asia',
        '알라인': 'Align',
        '팔라초': 'Palazzo',
        '그루브': 'Groove',
        '슈퍼': 'Super',
        '하이라이즈': 'High-Rise',
        '플레어드': 'Flared',
        '노라인': 'No Line',
        '스쿱백': 'Scoopback',
        '크롬': 'Chrome',
        '눌루': 'Nulu',
        '루온': 'Luon',
        '에버루': 'Everlux',
    }
    
    # 分割韩文名称并翻译每个部分
    translated_parts = []
    words = re.findall(r'[가-힣]+|[a-zA-Z]+|\d+', korean_name)
    
    for word in words:
        if word in translation_map:
            translated_parts.append(translation_map[word])
        else:
            # 如果找不到翻译，保留原词
            translated_parts.append(word)
    
    result = ' '.join(translated_parts)
    
    # 如果翻译结果和原名称相同，说明没有翻译成功
    if result == korean_name:
        return korean_name
    
    return result


def enhanced_manual_translation(korean_name):
    """
    增强的手动翻译方案 - 扩充的韩文到英文映射表
    包含更多Lululemon产品相关词汇
    """
    # 扩充的翻译映射表
    enhanced_map = {
        # 产品名称（完整匹配优先）
        '디파인 크롭 후드 재킷': 'Define Cropped Hooded Jacket',
        '디파인 재킷': 'Define Jacket',
        '디파인 오버사이즈드 재킷': 'Define Oversized Jacket',
        '크롭 디파인 재킷 리브드': 'Cropped Define Jacket Ribbed',
        '후드 디파인 재킷': 'Hooded Define Jacket',
        '디파인 크롭 후드 재킷 메쉬': 'Define Cropped Hooded Jacket Mesh',
        '후드 디파인 재킷 메쉬 벨트': 'Hooded Define Jacket Mesh Belt',
        '디파인 재킷 루온': 'Define Jacket Luon',
        '소프트 저지': 'Soft Jersey',
        '크루 넥': 'Crew Neck',
        '하프 집': 'Half Zip',
        '풀 집': 'Full Zip',
        '오버사이즈드': 'Oversized',
        '크롭': 'Cropped',
        '메쉬': 'Mesh',
        '벨트': 'Belt',
        '리브드': 'Ribbed',
        '루온': 'Luon',
        '눌루': 'Nulu',
        
        # 基础词汇
        '디파인': 'Define',
        '크롭': 'Cropped',
        '후드': 'Hooded',
        '재킷': 'Jacket',
        '메쉬': 'Mesh',
        '벨트': 'Belt',
        '소프트': 'Soft',
        '저지': 'Jersey',
        '클래식': 'Classic',
        '팬츠': 'Pants',
        '셔츠': 'Shirt',
        '후디': 'Hoodie',
        '조거': 'Jogger',
        '스웨트': 'Sweat',
        '크루': 'Crew',
        '탱크': 'Tank',
        '티셔츠': 'T-Shirt',
        '풀오버': 'Pullover',
        '스테디': 'Steady',
        '스테이트': 'State',
        '트레이닝': 'Training',
        '러닝': 'Running',
        '요가': 'Yoga',
        '워크아웃': 'Workout',
        '오버사이즈': 'Oversized',
        '리브드': 'Ribbed',
        '맨스': "Men's",
        '우먼스': "Women's",
        '넥': 'Neck',
        '집': 'Zip',
        '하프': 'Half',
        '풀': 'Full',
        
        # 新增缺失的词汇
        '핏': 'Fit',
        '롱슬리브': 'Long Sleeve',
        '쇼츠': 'Shorts',
        '숏슬리브': 'Short Sleeve',
        '롱': 'Long',
        '숏': 'Short',
        '슬리브': 'Sleeve',
        '레귤러': 'Regular',
        '아시아': 'Asia',
        '알라인': 'Align',
        '팔라초': 'Palazzo',
        '그루브': 'Groove',
        '슈퍼': 'Super',
        '하이라이즈': 'High-Rise',
        '플레어드': 'Flared',
        '노라인': 'No Line',
        '스쿱백': 'Scoopback',
        '크롬': 'Chrome',
        '눌루': 'Nulu',
        '루온': 'Luon',
        '에버루': 'Everlux',
        '스웨트': 'Sweat',
        '스웨트셔츠': 'Sweatshirt',
        '스웨트팬츠': 'Sweatpants',
        '스웨트쇼츠': 'Sweatshorts',
        '스웨트후디': 'Sweathoodie',
        '스웨트조거': 'Sweatjogger',
        '스웨트탱크': 'Sweattank',
        '스웨트티': 'Sweattee',
        '스웨트크루': 'Sweatcrew',
        '스웨트풀오버': 'Sweatpullover',
        '스웨트집': 'Sweatzip',
        '스웨트하프집': 'Sweathalfzip',
        '스웨트풀집': 'Sweatfullzip',
        '스웨트오버사이즈': 'Sweatoversized',
        '스웨트크롭': 'Sweatcropped',
        '스웨트후드': 'Sweathooded',
        '스웨트메쉬': 'Sweatmesh',
        '스웨트벨트': 'Sweatbelt',
        '스웨트리브드': 'Sweatribbed',
        '스웨트루온': 'Sweatluon',
        '스웨트눌루': 'Sweatnulu',
        '스웨트에버루': 'Sweateverlux',
        '스웨트맨스': "Men's Sweat",
        '스웨트우먼스': "Women's Sweat",
        '스웨트넥': 'Sweatneck',
        '스웨트집': 'Sweatzip',
        '스웨트하프': 'Sweathalf',
        '스웨트풀': 'Sweatfull',
    }
    
    # 先尝试完整匹配
    if korean_name in enhanced_map:
        return enhanced_map[korean_name]
    
    # 如果没有完整匹配，尝试分词翻译
    translated_parts = []
    words = re.findall(r'[가-힣]+|[a-zA-Z]+|\d+', korean_name)
    
    for word in words:
        if word in enhanced_map:
            translated_parts.append(enhanced_map[word])
        else:
            # 保留原词
            translated_parts.append(word)
    
    result = ' '.join(translated_parts)
    
    # 如果翻译结果还是包含大量韩文，返回原名称
    if result == korean_name or len([w for w in words if re.match(r'[가-힣]+', w)]) > len(words) / 2:
        return korean_name  # 返回原始韩文名称，至少能显示
    
    return result


def extract_and_translate_product_name(url_encoded_name, show_progress=True):
    """
    从URL编码的产品名称中提取并翻译
    """
    try:
        # URL解码获取原始韩文名称
        korean_name = urllib.parse.unquote(url_encoded_name)
        # HTML实体解码（如果有的话）
        korean_name = html.unescape(korean_name)
        
        # 翻译为英文
        english_name = translate_korean_to_english(korean_name, show_progress)
        
        return {
            'korean_name': korean_name,
            'english_name': english_name,
            'original_encoded': url_encoded_name
        }
    except Exception as e:
        print(f"产品名称提取和翻译失败: {e}")
        return {
            'korean_name': url_encoded_name,
            'english_name': 'Translation Failed',
            'original_encoded': url_encoded_name
        }


def get_product_translation(product_name, show_progress=True):
    """
    获取产品翻译的简化接口
    如果输入已经是韩文，直接翻译
    如果是URL编码，先解码再翻译
    """
    if '%' in product_name:
        # URL编码的产品名称
        return extract_and_translate_product_name(product_name, show_progress)
    else:
        # 直接的韩文产品名称
        english_name = translate_korean_to_english(product_name, show_progress)
        return {
            'korean_name': product_name,
            'english_name': english_name,
            'original_encoded': product_name
        }


def batch_translate_products(product_names, show_progress=True):
    """
    批量翻译产品名称
    """
    if show_progress:
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text(f"🔄 开始批量翻译 {len(product_names)} 个产品...")
    
    results = []
    for i, product_name in enumerate(product_names):
        if show_progress:
            progress = int((i + 1) / len(product_names) * 100)
            progress_bar.progress(progress)
            status_text.text(f"🔄 翻译进度: {i+1}/{len(product_names)} - {product_name[:30]}...")
        
        result = get_product_translation(product_name, show_progress=False)
        results.append(result)
    
    if show_progress:
        progress_bar.progress(100)
        status_text.text("✅ 批量翻译完成")
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
    
    return results


def test_translation_engines():
    """
    测试所有翻译引擎的可用性
    """
    test_text = "디파인 재킷"
    translators = [
        ('bing', 'Bing翻译'),
        ('baidu', '百度翻译'),
        ('google', '谷歌翻译'),
        ('netease', '网易翻译')
    ]
    
    results = {}
    for translator_name, translator_display in translators:
        try:
            print(f"测试 {translator_display}...")
            result = ts.translate_text(
                test_text,
                from_language='ko',
                to_language='en',
                translator=translator_name,
            )
            results[translator_display] = {'status': 'success', 'result': result}
            print(f"✅ {translator_display}: {result}")
        except Exception as e:
            results[translator_display] = {'status': 'failed', 'error': str(e)}
            print(f"❌ {translator_display}: {e}")
    
    return results


# 测试函数
def test_translation():
    """
    测试翻译功能
    """
    test_cases = [
        "소프트 저지 클래식 핏 팬츠",
        "스테디 스테이트 후디",
        "맨스 트레이닝 셔츠",
        "우먼스 요가 팬츠",
        "크루 넥 스웨트셔츠"
    ]
    
    print("=== 产品名称翻译测试 ===")
    for korean_name in test_cases:
        result = get_product_translation(korean_name, show_progress=False)
        print(f"韩文: {result['korean_name']}")
        print(f"英文: {result['english_name']}")
        print("-" * 50)


if __name__ == "__main__":
    test_translation()

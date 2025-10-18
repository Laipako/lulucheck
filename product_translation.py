import urllib.parse
import html
import translators as ts
import re


def translate_korean_to_english(korean_name):
    """
    将韩语产品名称翻译为英语
    使用多种翻译方法确保准确性
    """
    try:
        # 方法1: 使用bing翻译服务
        print(f"正在翻译: {korean_name}")
        english_name = ts.translate_text(
            korean_name,
            from_language='ko',
            to_language='en',
            translator='bing',
        )
        print(f"翻译成功: {korean_name} -> {english_name}")
        return english_name
    except Exception as e:
        print(f"翻译服务失败: {e}")
        # 方法2: 使用手动翻译备用方案
        fallback_result = manual_translation_fallback(korean_name)
        print(f"使用备用翻译: {korean_name} -> {fallback_result}")
        return fallback_result


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
    
    return ' '.join(translated_parts)


def extract_and_translate_product_name(url_encoded_name):
    """
    从URL编码的产品名称中提取并翻译
    """
    try:
        # URL解码获取原始韩文名称
        korean_name = urllib.parse.unquote(url_encoded_name)
        # HTML实体解码（如果有的话）
        korean_name = html.unescape(korean_name)
        
        # 翻译为英文
        english_name = translate_korean_to_english(korean_name)
        
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


def get_product_translation(product_name):
    """
    获取产品翻译的简化接口
    如果输入已经是韩文，直接翻译
    如果是URL编码，先解码再翻译
    """
    if '%' in product_name:
        # URL编码的产品名称
        return extract_and_translate_product_name(product_name)
    else:
        # 直接的韩文产品名称
        english_name = translate_korean_to_english(product_name)
        return {
            'korean_name': product_name,
            'english_name': english_name,
            'original_encoded': product_name
        }


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
        result = get_product_translation(korean_name)
        print(f"韩文: {result['korean_name']}")
        print(f"英文: {result['english_name']}")
        print("-" * 50)


if __name__ == "__main__":
    test_translation()

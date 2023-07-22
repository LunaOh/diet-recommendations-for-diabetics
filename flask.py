from flask import Flask, request, render_template, jsonify, redirect, url_for
import pandas as pd
import numpy as np
import os
from flask_cors import CORS
from urllib.parse import quote

#app = Flask(__name__, template_folder='/Users/dajungoh/opt/anaconda3/pkgs/holoviews-1.14.8-pyhd3eb1b0_0/site-packages/holoviews/examples/gallery/apps/flask/templates')

app = Flask(__name__)
app.template_folder = '/Users/dajungoh/Downloads/templates 2'
app.static_folder = '/Users/dajungoh/Downloads/templates 2'
cors = CORS(app)
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'  # 특정 도메인을 허용하려면 '*' 대신 허용할 도메인을 지정
    response.headers['Access-Control-Allow-Methods'] = 'POST'  # 허용할 HTTP 메서드를 지정
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'  # 허용할 헤더를 지정
    return response


@app.route('/')
def index():
    return render_template('신체테스트/TestPage_h.html')

@app.route('/recommend', methods=['POST'])
def recommend_meal():
    # Content-Type 확인
    if request.headers.get('Content-Type') != 'application/json':
        return jsonify({'error': 'Unsupported Media Type'}), 415

    # 파일 경로
    file_path = os.path.join('data', '캡스톤_당뇨식단.xlsx')
    # 파일 읽기
    data = pd.read_excel(file_path)
    data = data.fillna(0)

    # AJAX 요청으로부터 데이터를 받아옴
    request_data = request.json
    preference_meat = int(request_data['preference_meat'])
    preference_fish = int(request_data['preference_fish'])
    preference_noodles = int(request_data['preference_noodles'])
    preference_rice = int(request_data['preference_rice'])
    preference_spicy = int(request_data['preference_spicy'])
    gender = request_data['gender']
    height = int(request_data['height'])
    weight = int(request_data['weight'])
    activity_level = request_data['activity_level']

    # 표준체중 및 1일 총 열량 계산
    if gender == '남성':
        standard_weight = (height / 100) ** 2 * 22
    else:
        standard_weight = (height / 100) ** 2 * 21

    if activity_level == '가벼운 활동':
        calorie_range = (standard_weight * 25, standard_weight * 30)
    elif activity_level == '중증도 활동':
        calorie_range = (standard_weight * 30, standard_weight * 35)
    elif activity_level == '심한 활동':
        calorie_range = (standard_weight * 35, standard_weight * 40)
    else:
        return jsonify({'error': '잘못된 활동량을 입력하셨습니다.'})

    # 필요한 열량 계산
    target_calories = (calorie_range[0] + calorie_range[1]) / 2  # 필요한 열량 범위의 중간값으로 설정

    # 필요한 열만 선택
    filtered_data = data[['하루칼로리', '메뉴구분', '메뉴1', '메뉴2', '메뉴3', '메뉴4', '메뉴5', '메뉴6', '육류', '어류', '면류', '밥류', '매운맛']]

    # 추천 식단 생성
    if target_calories <= 1500:
        recommended_calories = 1400
    elif target_calories <= 1700:
        recommended_calories = 1600
    elif target_calories <= 1900:
        recommended_calories = 1800
    else:
        recommended_calories = 2000

    # 아침, 점심, 저녁 식단 추천
    filtered_data_meals = filtered_data[
        (filtered_data['메뉴구분'] == '아침') |
        (filtered_data['메뉴구분'] == '점심') |
        (filtered_data['메뉴구분'] == '저녁')
        ]

    filtered_data_meals = filtered_data_meals[
        (filtered_data_meals['하루칼로리'] == recommended_calories) &
        (
                (
                        (preference_meat == 1) & ((filtered_data_meals['육류'] == 1) | (filtered_data_meals['육류'] == 0)) |
                        (preference_fish == 1) & ((filtered_data_meals['어류'] == 1) | (filtered_data_meals['어류'] == 0)) |
                        (preference_noodles == 1) & ((filtered_data_meals['면류'] == 1) | (filtered_data_meals['면류'] == 0)) |
                        (preference_rice == 1) & ((filtered_data_meals['밥류'] == 1) | (filtered_data_meals['밥류'] == 0)) |
                        (preference_spicy == 1) & ((filtered_data_meals['매운맛'] == 1) | (filtered_data_meals['매운맛'] == 0))
                ) |
                (
                        (preference_meat == 0) & (preference_fish == 0) & (preference_noodles == 0) & (preference_rice == 0) & (preference_spicy == 0)
                )
        ) &
        (
            ~(
                    (preference_meat == 0) & (filtered_data_meals['육류'] == 1) |
                    (preference_fish == 0) & (filtered_data_meals['어류'] == 1) |
                    (preference_noodles == 0) & (filtered_data_meals['면류'] == 1) |
                    (preference_rice == 0) & (filtered_data_meals['밥류'] == 1) |
                    (preference_spicy == 0) & (filtered_data_meals['매운맛'] == 1)
            )
        )
        ]

    # 아침, 점심, 저녁 각각 1개의 식단 랜덤 추천
    recommended_meals = []
    meal_types = ['아침', '점심', '저녁']
    for meal_type in meal_types:
        filtered_meals_type = filtered_data_meals[filtered_data_meals['메뉴구분'] == meal_type]
        if len(filtered_meals_type) > 0:
            random_meal_index = np.random.randint(0, len(filtered_meals_type))
            recommended_meal = filtered_meals_type.iloc[random_meal_index]
            recommended_meals.append(recommended_meal)
        else:
            # 추천되는 식단이 없는 경우 다른 식단 카테고리에서 선택
            other_meal_types = [m for m in meal_types if m != meal_type]
            for other_meal_type in other_meal_types:
                filtered_meals_type = filtered_data_meals[filtered_data_meals['메뉴구분'] == other_meal_type]
                if len(filtered_meals_type) > 0:
                    random_meal_index = np.random.randint(0, len(filtered_meals_type))
                    recommended_meal = filtered_meals_type.iloc[random_meal_index]
                    recommended_meals.append(recommended_meal)
                    break

    # 간식 식단 추천
    filtered_data_snacks = filtered_data[filtered_data['메뉴구분'] == '간식']
    result_str = ""

    if len(filtered_data_snacks) > 0:
        random_snack_index1 = np.random.randint(0, len(filtered_data_snacks))
        recommended_snack1 = filtered_data_snacks.iloc[random_snack_index1]
        recommended_meals.insert(2, recommended_snack1)

        # 다른 간식 식단 추천
        filtered_data_snacks2 = filtered_data_snacks[filtered_data_snacks.index != random_snack_index1]
        if len(filtered_data_snacks2) > 0:
            random_snack_index2 = np.random.randint(0, len(filtered_data_snacks2))
            recommended_snack2 = filtered_data_snacks2.iloc[random_snack_index2]
            recommended_meals.append(recommended_snack2)
        else:
            recommended_meals.append(recommended_snack1)
            result_str += "다른 간식 식단이 없어 같은 간식 식단이 중복으로 추가되었습니다."
    else:
        result_str += "추천할 간식이 없습니다."

    # 최종 추천 식단 결과 출력
    result_str += "=== 추천 식단 ===\n"
    meal_types = ['아침', '점심', '간식', '저녁', '간식']
    for meal_type, meal in zip(meal_types, recommended_meals):
        menu = [meal[f'메뉴{i + 1}'] for i in range(6)]
        menu_str = ', '.join([m if str(m) != '0' else '' for m in menu])
        result_str += f"{meal_type}: {menu_str.replace(', ,', '')}\n"

    # CORS 헤더 추가
    response = jsonify({'result_str': result_str})
    response = add_cors_headers(response)

    return response

    # 결과 반환
    #return render_template('신체테스트/HealthTest.html', result_str=result_str)

if __name__ == '__main__':
    app.run(port=8000, debug=True)

#!/usr/bin/env python3
"""
Скрипт инициализации базы данных TastySkills
Создает демо-ресторан "Варенье и Икра" с полным меню русской кухни
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.infrastructure.database.database import engine, SessionLocal
from app.domain.entities.models import Base, User, Restaurant, Section, Category, Product
from app.domain.entities.schemas import RestaurantCreate, SectionCreate, CategoryCreate, ProductCreate
from app.infrastructure.repositories.crud import (
    create_restaurant, create_section, create_category, create_product
)


def init_db() -> None:
    """Инициализация базы данных с демо-данными"""
    print("Инициализация базы данных TastySkills...")
    
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже данные
        existing_restaurants = db.query(Restaurant).count()
        if existing_restaurants > 0:
            print("База данных уже содержит данные. Пропускаем инициализацию.")
            return
        
        print("Создание демо-ресторана...")
        
        # Создаем демо-ресторан "Варенье & Икра" без привязки к пользователям
        restaurant_data = RestaurantCreate(
            name="Варенье & Икра",
            concept="Аутентичная русская кухня в современной интерпретации. Традиционные блюда с авторским подходом, домашние рецепты и сезонные ингредиенты.",
            manager_id=None,
            waiter_id=None
        )
        restaurant = create_restaurant(db, restaurant_data)
        print(f"Создан ресторан: {restaurant.name}")
        
        print("Создание разделов...")
        
        # Создаем разделы
        sections_data = [
            {
                "name": "Бар",
                "description": "Традиционные русские напитки, настойки, медовуха и авторские коктейли"
            },
            {
                "name": "Кухня", 
                "description": "Классические блюда русской кухни от закусок до десертов"
            }
        ]
        
        sections = {}
        for section_data in sections_data:
            section_create = SectionCreate(
                name=section_data["name"],
                description=section_data["description"],
                restaurant_id=restaurant.id  # type: ignore
            )
            created_section = create_section(db, section_create)
            sections[section_data["name"]] = created_section
            print(f"Создан раздел: {created_section.name}")
        
        print("Создание категорий и блюд...")
        
        # Данные для категорий и блюд
        menu_data = {
            "Бар": {
                "Крепкие напитки": [
                    {
                        "title": "Водка 'Мороз'",
                        "weight": "50мл",
                        "ingredients": "Водка премиум класса, настоянная на травах",
                        "description": "Традиционная русская водка с добавлением ароматных трав",
                        "features": "Подается охлажденной до -18°C. Традиционно закусывается соленым огурцом или черным хлебом с салом.",
                        "table_setting": "В хрустальной рюмке на льду",
                        "gastronomic_pairings": "Соленые огурцы, черный хлеб, сало"
                    },
                    {
                        "title": "Настойка 'Березовый сок'",
                        "weight": "50мл", 
                        "ingredients": "Березовый сок, водка, мед, лимон",
                        "description": "Домашняя настойка на березовом соке с медом",
                        "features": "Готовится по старинному рецепту. Березовый сок собирается ранней весной, когда дерево просыпается.",
                        "table_setting": "В глиняном кувшине",
                        "gastronomic_pairings": "Мед, лесные ягоды"
                    },
                    {
                        "title": "Медовуха 'Старая Русь'",
                        "weight": "300мл",
                        "ingredients": "Мед, вода, хмель, дрожжи",
                        "description": "Традиционный русский медовый напиток",
                        "features": "Готовится по рецепту XVI века. Созревает в дубовых бочках 3 месяца.",
                        "table_setting": "В деревянной кружке",
                        "gastronomic_pairings": "Медовые пряники, орехи"
                    }
                ],
                "Безалкогольные напитки": [
                    {
                        "title": "Квас 'Домашний'",
                        "weight": "500мл",
                        "ingredients": "Ржаной хлеб, сахар, изюм, дрожжи",
                        "description": "Традиционный русский квас домашнего приготовления",
                        "features": "Готовится на ржаном хлебе по старинному рецепту. Освежающий и полезный напиток.",
                        "table_setting": "В глиняном кувшине с деревянной кружкой",
                        "gastronomic_pairings": "Черный хлеб, соленые огурцы"
                    },
                    {
                        "title": "Морс 'Клюквенный'",
                        "weight": "300мл",
                        "ingredients": "Клюква, сахар, вода, мед",
                        "description": "Освежающий морс из северной клюквы",
                        "features": "Клюква собирается вручную в северных лесах. Богат витамином C.",
                        "table_setting": "В хрустальном стакане со льдом",
                        "gastronomic_pairings": "Медовые пряники, орехи"
                    },
                    {
                        "title": "Сбитень 'Пряный'",
                        "weight": "250мл",
                        "ingredients": "Мед, вода, корица, гвоздика, имбирь",
                        "description": "Традиционный горячий напиток с пряностями",
                        "features": "Сбитень - древнерусский напиток, упоминаемый в летописях. Согревает и укрепляет иммунитет.",
                        "table_setting": "В глиняной кружке горячим",
                        "gastronomic_pairings": "Медовые пряники, сухофрукты"
                    }
                ],
                "Коктейли": [
                    {
                        "title": "Коктейль 'Москва'",
                        "weight": "200мл",
                        "ingredients": "Водка, клюквенный морс, мед, лимон",
                        "description": "Авторский коктейль в русском стиле",
                        "features": "Создан специально для нашего ресторана. Сочетает традиционные русские ингредиенты.",
                        "table_setting": "В хрустальном бокале с долькой лимона",
                        "gastronomic_pairings": "Соленые огурцы, черная икра"
                    },
                    {
                        "title": "Коктейль 'Бабье лето'",
                        "weight": "250мл",
                        "ingredients": "Медовуха, яблочный сок, корица",
                        "description": "Осенний коктейль с медовухой",
                        "features": "Название связано с теплой осенней погодой. Подается в сезон сбора урожая.",
                        "table_setting": "В медной кружке с палочкой корицы",
                        "gastronomic_pairings": "Печеные яблоки, мед"
                    },
                    {
                        "title": "Коктейль 'Зимний вечер'",
                        "weight": "200мл",
                        "ingredients": "Водка, горячий чай, мед, лимон",
                        "description": "Согревающий зимний коктейль",
                        "features": "Идеален для холодных зимних вечеров. Согревает и поднимает настроение.",
                        "table_setting": "В фарфоровой кружке горячим",
                        "gastronomic_pairings": "Медовые пряники, варенье"
                    }
                ]
            },
            "Кухня": {
                "Закуски": [
                    {
                        "title": "Сельдь под шубой",
                        "weight": "200г",
                        "ingredients": "Сельдь, картофель, морковь, свекла, майонез, лук",
                        "description": "Классическая русская закуска из сельди с овощами",
                        "features": "Блюдо появилось в 1918 году в московском ресторане. Слои символизируют цвета революционного флага.",
                        "table_setting": "В стеклянной салатнице с ложкой",
                        "gastronomic_pairings": "Черный хлеб, водка"
                    },
                    {
                        "title": "Холодец 'Домашний'",
                        "weight": "250г",
                        "ingredients": "Свиные ножки, говядина, морковь, лук, чеснок, специи",
                        "description": "Традиционный русский холодец с мясом",
                        "features": "Готовится 8 часов на медленном огне. Богат коллагеном и полезен для суставов.",
                        "table_setting": "На деревянной доске с хреном и горчицей",
                        "gastronomic_pairings": "Хрен, горчица, черный хлеб"
                    },
                    {
                        "title": "Икра красная 'Камчатская'",
                        "weight": "50г",
                        "ingredients": "Красная икра лосося, соль",
                        "description": "Премиальная красная икра с Камчатки",
                        "features": "Икра добывается в экологически чистых водах Камчатки. Солится по старинному рецепту.",
                        "table_setting": "В хрустальной икорнице с перламутровой ложкой",
                        "gastronomic_pairings": "Блины, сметана, водка"
                    }
                ],
                "Супы": [
                    {
                        "title": "Борщ 'По-русски'",
                        "weight": "400г",
                        "ingredients": "Свекла, капуста, картофель, морковь, лук, говядина, сметана",
                        "description": "Классический борщ с говядиной и сметаной",
                        "features": "Готовится на говяжьем бульоне с добавлением сала. Свекла придает характерный цвет.",
                        "table_setting": "В глиняной миске с сметаной и чесночными пампушками",
                        "gastronomic_pairings": "Чесночные пампушки, сало, сметана"
                    },
                    {
                        "title": "Щи 'Кислые'",
                        "weight": "350г",
                        "ingredients": "Квашеная капуста, картофель, морковь, лук, грибы, сметана",
                        "description": "Традиционные кислые щи с квашеной капустой",
                        "features": "Квашеная капуста готовится по старинному рецепту. Богата витамином C.",
                        "table_setting": "В глиняной миске с ржаным хлебом",
                        "gastronomic_pairings": "Ржаной хлеб, сметана, сало"
                    },
                    {
                        "title": "Уха 'Рыбацкая'",
                        "weight": "400г",
                        "ingredients": "Речная рыба, картофель, морковь, лук, зелень, водка",
                        "description": "Наваристая уха из речной рыбы",
                        "features": "Готовится из трех видов рыбы. В конце добавляется рюмка водки для аромата.",
                        "table_setting": "В глиняной миске с зеленью",
                        "gastronomic_pairings": "Черный хлеб, водка"
                    }
                ],
                "Основные блюда": [
                    {
                        "title": "Бефстроганов 'Классический'",
                    "weight": "300г",
                        "ingredients": "Говядина, сметана, грибы, лук, горчица, специи",
                        "description": "Классический бефстроганов в сметанном соусе",
                        "features": "Блюдо названо в честь графа Строганова. Говядина нарезается тонкими полосками.",
                        "table_setting": "В фарфоровой тарелке с гречневой кашей",
                        "gastronomic_pairings": "Гречневая каша, соленые огурцы"
                    },
                    {
                        "title": "Котлеты 'Пожарские'",
                        "weight": "250г",
                        "ingredients": "Куриное филе, сливочное масло, хлеб, лук, специи",
                        "description": "Классические пожарские котлеты из курицы",
                        "features": "Рецепт XIX века из трактира Пожарского в Торжке. Котлеты обжариваются в сухарях.",
                        "table_setting": "На деревянной доске с картофельным пюре",
                        "gastronomic_pairings": "Картофельное пюре, клюквенный соус"
                    },
                    {
                        "title": "Гусь 'Печеный'",
                        "weight": "400г",
                        "ingredients": "Гусь, яблоки, мед, специи, чеснок",
                        "description": "Печеный гусь с яблоками и медом",
                        "features": "Гусь фаршируется кислыми яблоками и запекается с медом. Традиционное блюдо на Рождество.",
                        "table_setting": "На большом блюде с запеченными яблоками",
                        "gastronomic_pairings": "Квашеная капуста, клюквенный соус"
                    }
                ],
                "Гарниры": [
                    {
                        "title": "Гречка 'По-купечески'",
                    "weight": "200г",
                        "ingredients": "Гречневая крупа, грибы, лук, морковь, масло",
                        "description": "Гречка с грибами в традиционном исполнении",
                        "features": "Готовится в горшочке в печи. Грибы придают особый аромат.",
                        "table_setting": "В глиняном горшочке",
                        "gastronomic_pairings": "Сметана, соленые огурцы"
                    },
                    {
                        "title": "Картошка 'В мундире'",
                        "weight": "300г",
                        "ingredients": "Картофель, соль, масло, зелень",
                        "description": "Отварной картофель в мундире с маслом",
                        "features": "Картофель варится в кожуре, что сохраняет витамины. Подается с растопленным маслом.",
                        "table_setting": "В деревянной миске с маслом",
                        "gastronomic_pairings": "Сметана, зелень, сало"
                    },
                    {
                        "title": "Каша 'Пшенная'",
                        "weight": "250г",
                        "ingredients": "Пшено, молоко, масло, мед, изюм",
                        "description": "Сладкая пшенная каша с медом и изюмом",
                        "features": "Традиционная русская каша. Пшено богато витаминами группы B.",
                        "table_setting": "В глиняной миске с медом",
                        "gastronomic_pairings": "Мед, изюм, орехи"
                    }
                ],
                "Десерты": [
                    {
                        "title": "Блины 'Масленичные'",
                    "weight": "300г",
                        "ingredients": "Мука, молоко, яйца, масло, соль, сахар",
                        "description": "Традиционные русские блины на Масленицу",
                        "features": "Готовятся на закваске. Каждый блин символизирует солнце. Традиционное блюдо Масленицы.",
                        "table_setting": "На деревянном блюде стопкой",
                        "gastronomic_pairings": "Сметана, мед, варенье, икра"
                    },
                    {
                        "title": "Медовик 'Классический'",
                        "weight": "200г",
                        "ingredients": "Мед, мука, яйца, сметана, сахар, корица",
                        "description": "Классический медовый торт с медовыми коржами",
                        "features": "Рецепт XIX века. Коржи пропитываются сметанным кремом. Созревает 24 часа.",
                        "table_setting": "На фарфоровой тарелке с медом",
                        "gastronomic_pairings": "Мед, чай, молоко"
                    },
                    {
                        "title": "Варенье 'Из лесных ягод'",
                        "weight": "100г",
                        "ingredients": "Лесные ягоды, сахар, лимонная кислота",
                        "description": "Домашнее варенье из лесных ягод",
                        "features": "Ягоды собираются вручную в северных лесах. Варенье готовится в медном тазу.",
                        "table_setting": "В хрустальной вазочке с серебряной ложкой",
                        "gastronomic_pairings": "Чай, блины, творог"
                    }
                ]
            }
        }
        
        # Создаем категории и блюда
        for section_name, categories_data in menu_data.items():
            section = sections[section_name]
            for category_name, products_data in categories_data.items():
                # Создаем категорию
                category_create = CategoryCreate(
                    title=category_name,
                    description=f"Традиционные {category_name.lower()} русской кухни",
                    section_id=section.id,  # type: ignore
                    restaurant_id=restaurant.id  # type: ignore
                )
                category = create_category(db, category_create)
                print(f"Создана категория: {category.title} в разделе {section.name}")
                
                # Создаем блюда в категории
                for product_data in products_data:
                    product_create = ProductCreate(
                        title=product_data["title"],
                        weight=product_data["weight"],
                        ingredients=product_data["ingredients"],
                        description=product_data["description"],
                        features=product_data["features"],
                        table_setting=product_data["table_setting"],
                        gastronomic_pairings=product_data["gastronomic_pairings"],
                        category_id=category.id,  # type: ignore
                        restaurant_id=restaurant.id  # type: ignore
                    )
                    product = create_product(db, product_create)
                    print(f"  Создано блюдо: {product.title}")
        
        print("\nИнициализация базы данных завершена успешно!")
        print(f"Создано:")
        print(f"   Ресторанов: 1 ('{restaurant.name}')")
        print(f"   Разделов: {len(sections)}")
        print(f"   Категорий: 8")
        print(f"   Блюд: 24")
        print(f"\nДемо-страница: http://localhost:8000/demo")
        print(f"Для создания собственного ресторана зарегистрируйтесь как менеджер.")
        
    except Exception as e:
        print(f"Ошибка при инициализации: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_db() 
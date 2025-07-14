from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.infrastructure.database.database import get_db
from app.presentation.api.auth import get_current_user_from_cookies, authenticate_user, create_access_token
from app.domain.entities.models import User
from app.infrastructure.repositories.crud import (
    get_restaurants, get_restaurant, get_sections_by_restaurant, get_section,
    get_categories_by_section, get_category, get_products_by_category, get_product,
    get_recent_products, create_section, update_section, delete_section,
    create_category, update_category, delete_category,
    create_product, update_product, delete_product,
    get_restaurants_by_manager, get_restaurants_by_waiter, create_restaurant,
    get_recent_products_by_restaurants, get_sections, get_products, get_users,
    get_first_product_by_category
)
from app.domain.entities.schemas import SectionCreate, SectionUpdate, CategoryCreate, CategoryUpdate, ProductCreate, ProductUpdate, RestaurantCreate
from typing import Optional, Any
from datetime import timedelta
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
import os
from fastapi import status
from fastapi import FastAPI
from starlette.exceptions import HTTPException

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_demo_restaurant_id(db: Session) -> Optional[int]:
    """Получение ID демо-ресторана (первый ресторан без привязки к пользователям)"""
    restaurants = get_restaurants(db, limit=1)
    if restaurants:
        restaurant = restaurants[0]
        # Проверяем, что это демо-ресторан (без manager_id и waiter_id)
        if restaurant.manager_id is None and restaurant.waiter_id is None:
            return int(restaurant.id)  # type: ignore
    return None


def check_manager_access(user: Optional[User]) -> None:
    """Проверка доступа менеджера"""
    if not user or user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Доступ запрещен. Требуются права менеджера.")


def check_restaurant_access(user: Optional[User], restaurant_id: int, db: Session) -> None:
    """Проверка доступа к ресторану"""
    # Проверяем, является ли это демо-рестораном
    demo_restaurant_id = get_demo_restaurant_id(db)
    if demo_restaurant_id and restaurant_id == demo_restaurant_id:
        # Демо-ресторан доступен всем
        return
    
    # Для остальных ресторанов требуется авторизация
    if not user:
        raise HTTPException(status_code=302, detail="Требуется авторизация", headers={"Location": "/login"})
    
    # Админы имеют доступ ко всем ресторанам
    if str(user.role) == "admin":  # type: ignore
        return
    
    # Проверяем доступ менеджера или официанта к ресторану
    if str(user.role) == "manager":  # type: ignore
        user_restaurants = get_restaurants_by_manager(db, user.id)  # type: ignore
    elif str(user.role) == "waiter":  # type: ignore
        user_restaurants = get_restaurants_by_waiter(db, user.id)  # type: ignore
    else:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    # Проверяем, есть ли у пользователя доступ к данному ресторану
    if not any(r.id == restaurant_id for r in user_restaurants):
        raise HTTPException(status_code=403, detail="Доступ к ресторану запрещен")


def check_section_access(user: Optional[User], section_id: int, db: Session) -> None:
    """Проверка доступа к разделу"""
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Раздел не найден")
    
    check_restaurant_access(user, section.restaurant_id, db)  # type: ignore


def check_category_access(user: Optional[User], category_id: int, db: Session) -> None:
    """Проверка доступа к категории"""
    category = get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    check_restaurant_access(user, category.restaurant_id, db)  # type: ignore


def check_product_access(user: Optional[User], product_id: int, db: Session) -> None:
    """Проверка доступа к продукту"""
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    check_restaurant_access(user, product.restaurant_id, db)  # type: ignore


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Главная страница"""
    current_user = get_current_user_from_cookies(request, db)
    
    # Если пользователь менеджер или официант, перенаправляем на его ресторан
    if current_user and str(current_user.role) in ['manager', 'waiter']:  # type: ignore
        if str(current_user.role) == 'manager':  # type: ignore
            user_restaurants = get_restaurants_by_manager(db, current_user.id)  # type: ignore
        else:
            user_restaurants = get_restaurants_by_waiter(db, current_user.id)  # type: ignore
        
        if user_restaurants:
            # Перенаправляем на ресторан пользователя
            return RedirectResponse(url=f"/restaurants/{user_restaurants[0].id}", status_code=302)
    
    # Для админов и неавторизованных пользователей показываем главную страницу
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": current_user
    })


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request) -> Any:
    """Страница о проекте"""
    return templates.TemplateResponse("about.html", {
        "request": request,
        "no_sidebar": True
    })


@router.get("/demo", response_class=HTMLResponse)
async def demo_page(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Демо-страница с примером ресторана"""
    # Получаем первый ресторан (демо-ресторан)
    restaurants = get_restaurants(db, limit=1)
    if not restaurants:
        raise HTTPException(status_code=404, detail="Demo restaurant not found")
    
    demo_restaurant = restaurants[0]
    sections = get_sections_by_restaurant(db, demo_restaurant.id)  # type: ignore
    
    return templates.TemplateResponse("restaurant_detail.html", {
        "request": request,
        "user": None,  # Неавторизованный пользователь
        "restaurant": demo_restaurant,
        "sections": sections,
        "is_demo": True  # Флаг для демо-режима
    })


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> Any:
    """Страница входа"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "no_sidebar": True
    })


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
) -> Any:
    """Обработка входа через веб-форму"""
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html", 
            {
                "request": request, 
                "error": "Неверное имя пользователя или пароль"
            }
        )
    
    # Создаем токен
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Перенаправляем на главную страницу с токеном в cookies
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,  # 30 минут
        samesite="lax"
    )
    return response


@router.get("/logout")
async def logout() -> Any:
    """Выход из системы"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.get("/restaurants", response_class=HTMLResponse)
async def restaurants_page(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Страница со списком ресторанов"""
    current_user = get_current_user_from_cookies(request, db)
    
    # Если пользователь не админ, перенаправляем на его ресторан
    if current_user and str(current_user.role) != 'admin':  # type: ignore
        if str(current_user.role) == 'manager':  # type: ignore
            user_restaurants = get_restaurants_by_manager(db, current_user.id)  # type: ignore
        elif str(current_user.role) == 'waiter':  # type: ignore
            user_restaurants = get_restaurants_by_waiter(db, current_user.id)  # type: ignore
        else:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if user_restaurants:
            # Перенаправляем на первый (и единственный) ресторан пользователя
            return RedirectResponse(url=f"/restaurants/{user_restaurants[0].id}", status_code=302)
        else:
            # Если у пользователя нет ресторана, показываем ошибку
            raise HTTPException(status_code=404, detail="Restaurant not found for user")
    
    # Только админы видят список всех ресторанов
    restaurants = get_restaurants(db)
    
    return templates.TemplateResponse("restaurants.html", {
        "request": request,
        "user": current_user,
        "restaurants": restaurants
    })


@router.get("/restaurants/{restaurant_id}", response_class=HTMLResponse)
async def restaurant_detail(
    request: Request,
    restaurant_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Детальная страница ресторана"""
    current_user = get_current_user_from_cookies(request, db)
    check_restaurant_access(current_user, restaurant_id, db)
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    sections = get_sections_by_restaurant(db, restaurant_id)
    demo_restaurant_id = get_demo_restaurant_id(db)
    is_demo = demo_restaurant_id and restaurant_id == demo_restaurant_id
    return templates.TemplateResponse("restaurant_detail.html", {
        "request": request,
        "user": current_user,
        "restaurant": restaurant,
        "sections": sections,
        "is_demo": is_demo
    })

@router.get("/restaurants/{restaurant_id}/sections/{section_id}", response_class=HTMLResponse)
async def section_detail(
    request: Request,
    restaurant_id: int,
    section_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Детальная страница раздела"""
    current_user = get_current_user_from_cookies(request, db)
    section = get_section(db, section_id)
    if section is None or int(getattr(section, 'restaurant_id', -1)) != int(restaurant_id):
        raise HTTPException(status_code=404, detail="Section not found or does not belong to restaurant")
    check_restaurant_access(current_user, restaurant_id, db)
    categories = get_categories_by_section(db, section_id)
    for cat in categories:
        cat_id = getattr(cat, 'id', None)
        if isinstance(cat_id, int):
            cat.first_product = get_first_product_by_category(db, cat_id)
        else:
            cat.first_product = None
    demo_restaurant_id = get_demo_restaurant_id(db)
    is_demo = demo_restaurant_id and restaurant_id == demo_restaurant_id
    return templates.TemplateResponse("section_detail.html", {
        "request": request,
        "user": current_user,
        "section": section,
        "categories": categories,
        "is_demo": is_demo
    })

@router.get("/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}", response_class=HTMLResponse)
async def category_detail(
    request: Request,
    restaurant_id: int,
    section_id: int,
    category_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Детальная страница категории"""
    current_user = get_current_user_from_cookies(request, db)
    category = get_category(db, category_id)
    if category is None or int(getattr(category, 'section_id', -1)) != int(section_id) or int(getattr(category, 'restaurant_id', -1)) != int(restaurant_id):
        raise HTTPException(status_code=404, detail="Category not found or does not belong to section/restaurant")
    check_restaurant_access(current_user, restaurant_id, db)
    products = get_products_by_category(db, category_id)
    demo_restaurant_id = get_demo_restaurant_id(db)
    is_demo = demo_restaurant_id and restaurant_id == demo_restaurant_id
    return templates.TemplateResponse("category_detail.html", {
        "request": request,
        "user": current_user,
        "category": category,
        "products": products,
        "is_demo": is_demo
    })

@router.get("/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}/products/{product_id}", response_class=HTMLResponse)
async def product_detail(
    request: Request,
    restaurant_id: int,
    section_id: int,
    category_id: int,
    product_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Детальная страница продукта"""
    current_user = get_current_user_from_cookies(request, db)
    product = get_product(db, product_id)
    if product is None or int(getattr(product, 'category_id', -1)) != int(category_id) or int(getattr(product, 'restaurant_id', -1)) != int(restaurant_id):
        raise HTTPException(status_code=404, detail="Product not found or does not belong to category/restaurant")
    # Проверяем, что категория и секция тоже соответствуют
    category = get_category(db, category_id)
    if category is None or int(getattr(category, 'section_id', -1)) != int(section_id) or int(getattr(category, 'restaurant_id', -1)) != int(restaurant_id):
        raise HTTPException(status_code=404, detail="Category not found or does not belong to section/restaurant")
    section = get_section(db, section_id)
    if section is None or int(getattr(section, 'restaurant_id', -1)) != int(restaurant_id):
        raise HTTPException(status_code=404, detail="Section not found or does not belong to restaurant")
    check_restaurant_access(current_user, restaurant_id, db)
    demo_restaurant_id = get_demo_restaurant_id(db)
    is_demo = demo_restaurant_id and restaurant_id == demo_restaurant_id
    return templates.TemplateResponse("product_detail.html", {
        "request": request,
        "user": current_user,
        "product": product,
        "is_demo": is_demo
    })


@router.get("/recent-changes", response_class=HTMLResponse)
async def recent_changes(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Страница с недавними изменениями"""
    current_user = get_current_user_from_cookies(request, db)
    
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Админы видят все изменения
    if str(current_user.role) == "admin":  # type: ignore
        recent_products = get_recent_products(db, limit=20)
    else:
        # Менеджеры и официанты видят только изменения в своих ресторанах
        if str(current_user.role) == "manager":  # type: ignore
            user_restaurants = get_restaurants_by_manager(db, current_user.id)  # type: ignore
        elif str(current_user.role) == "waiter":  # type: ignore
            user_restaurants = get_restaurants_by_waiter(db, current_user.id)  # type: ignore
        else:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        
        # Получаем ID ресторанов пользователя
        restaurant_ids = [r.id for r in user_restaurants]  # type: ignore
        recent_products = get_recent_products_by_restaurants(db, restaurant_ids, limit=20)  # type: ignore
    
    return templates.TemplateResponse("recent_changes.html", {
        "request": request,
        "user": current_user,
        "recent_products": recent_products
    })


# === УПРАВЛЕНИЕ РАЗДЕЛАМИ ===
@router.get("/restaurants/{restaurant_id}/manage/sections/create", response_class=HTMLResponse)
async def create_section_page(
    request: Request,
    restaurant_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Страница создания раздела"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к ресторану
    check_restaurant_access(current_user, restaurant_id, db)
    
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    return templates.TemplateResponse("manage/create_section.html", {
        "request": request,
        "user": current_user,
        "restaurant": restaurant
    })


@router.post("/restaurants/{restaurant_id}/manage/sections/create", response_class=HTMLResponse)
async def create_section_post(
    request: Request,
    restaurant_id: int,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
) -> Any:
    """Создание раздела"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к ресторану
    check_restaurant_access(current_user, restaurant_id, db)
    
    section_data = SectionCreate(
        name=name,
        description=description,
        restaurant_id=restaurant_id
    )
    
    new_section = create_section(db, section_data)
    return RedirectResponse(url=f"/restaurants/{restaurant_id}", status_code=302)

@router.get("/restaurants/{restaurant_id}/sections/{section_id}/manage/edit", response_class=HTMLResponse)
async def edit_section_page(
    request: Request,
    restaurant_id: int,
    section_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Страница редактирования раздела"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к разделу
    check_section_access(current_user, section_id, db)
    
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    return templates.TemplateResponse("manage/edit_section.html", {
        "request": request,
        "user": current_user,
        "section": section
    })


@router.post("/restaurants/{restaurant_id}/sections/{section_id}/manage/edit", response_class=HTMLResponse)
async def edit_section_post(
    request: Request,
    restaurant_id: int,
    section_id: int,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
) -> Any:
    """Редактирование раздела"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к разделу
    check_section_access(current_user, section_id, db)
    
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    section_update = SectionUpdate(name=name, description=description)
    update_section(db, section_id, section_update)
    
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section_id}", status_code=302)


@router.post("/restaurants/{restaurant_id}/sections/{section_id}/manage/delete", response_class=HTMLResponse)
async def delete_section_post(
    request: Request,
    restaurant_id: int,
    section_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Удаление раздела"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к разделу
    check_section_access(current_user, section_id, db)
    
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    restaurant_id = int(getattr(section, 'restaurant_id', -1))
    delete_section(db, section_id)
    
    return RedirectResponse(url=f"/restaurants/{restaurant_id}", status_code=302)


# === УПРАВЛЕНИЕ КАТЕГОРИЯМИ ===
@router.get("/restaurants/{restaurant_id}/sections/{section_id}/manage/categories/create", response_class=HTMLResponse)
async def create_category_page(
    request: Request,
    restaurant_id: int,
    section_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Страница создания категории"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к разделу
    check_section_access(current_user, section_id, db)
    
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    return templates.TemplateResponse("manage/create_category.html", {
        "request": request,
        "user": current_user,
        "section": section
    })


@router.post("/restaurants/{restaurant_id}/sections/{section_id}/manage/categories/create", response_class=HTMLResponse)
async def create_category_post(
    request: Request,
    restaurant_id: int,
    section_id: int,
    title: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
) -> Any:
    """Создание категории"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к разделу
    check_section_access(current_user, section_id, db)
    
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    category_data = CategoryCreate(
        title=title,
        description=description,
        section_id=section_id,
        restaurant_id=section.restaurant_id  # type: ignore
    )
    
    new_category = create_category(db, category_data)
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section_id}", status_code=302)

@router.get("/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}/manage/edit", response_class=HTMLResponse)
async def edit_category_page(
    request: Request,
    restaurant_id: int,
    section_id: int,
    category_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Страница редактирования категории"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к категории
    check_category_access(current_user, category_id, db)
    
    category = get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return templates.TemplateResponse("manage/edit_category.html", {
        "request": request,
        "user": current_user,
        "category": category
    })


@router.post("/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}/manage/edit", response_class=HTMLResponse)
async def edit_category_post(
    request: Request,
    restaurant_id: int,
    section_id: int,
    category_id: int,
    title: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
) -> Any:
    """Редактирование категории"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к категории
    check_category_access(current_user, category_id, db)
    
    category = get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category_update = CategoryUpdate(title=title, description=description)
    update_category(db, category_id, category_update)
    
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}", status_code=302)


@router.post("/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}/manage/delete", response_class=HTMLResponse)
async def delete_category_post(
    request: Request,
    restaurant_id: int,
    section_id: int,
    category_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Удаление категории"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к категории
    check_category_access(current_user, category_id, db)
    
    category = get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    section_id = int(getattr(category, 'section_id', -1))
    delete_category(db, category_id)
    
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section_id}", status_code=302)


# === УПРАВЛЕНИЕ ПРОДУКТАМИ ===
@router.get("/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}/manage/products/create", response_class=HTMLResponse)
async def create_product_page(
    request: Request,
    restaurant_id: int,
    section_id: int,
    category_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Страница создания продукта"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к категории
    check_category_access(current_user, category_id, db)
    
    category = get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Проверяем, есть ли параметр success в URL
    success = request.query_params.get("success") == "true"
    
    return templates.TemplateResponse("manage/create_product.html", {
        "request": request,
        "user": current_user,
        "category": category,
        "success": success
    })


@router.post("/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}/manage/products/create", response_class=HTMLResponse)
async def create_product_post(
    request: Request,
    restaurant_id: int,
    section_id: int,
    category_id: int,
    title: str = Form(...),
    weight: str = Form(""),
    ingredients: str = Form(...),
    allergens: str = Form(""),
    description: str = Form(""),
    features: str = Form(""),
    table_setting: str = Form(""),
    gastronomic_pairings: str = Form(""),
    db: Session = Depends(get_db)
) -> Any:
    """Создание продукта"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к категории
    check_category_access(current_user, category_id, db)
    
    category = get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    product_data = ProductCreate(
        title=title,
        weight=weight if weight else None,
        ingredients=ingredients,
        allergens=allergens if allergens else None,
        description=description if description else None,
        features=features if features else None,
        table_setting=table_setting if table_setting else None,
        gastronomic_pairings=gastronomic_pairings if gastronomic_pairings else None,
        category_id=category_id,
        restaurant_id=category.restaurant_id  # type: ignore
    )
    
    create_product(db, product_data)
    # Перенаправляем обратно на страницу создания блюда с сообщением об успехе
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}?success=true", status_code=302)

@router.get("/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}/products/{product_id}/manage/edit", response_class=HTMLResponse)
async def edit_product_page(
    request: Request,
    restaurant_id: int,
    section_id: int,
    category_id: int,
    product_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Страница редактирования продукта"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к продукту
    check_product_access(current_user, product_id, db)
    
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return templates.TemplateResponse("manage/edit_product.html", {
        "request": request,
        "user": current_user,
        "product": product
    })


@router.post("/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}/products/{product_id}/manage/edit", response_class=HTMLResponse)
async def edit_product_post(
    request: Request,
    restaurant_id: int,
    section_id: int,
    category_id: int,
    product_id: int,
    title: str = Form(...),
    weight: str = Form(""),
    ingredients: str = Form(...),
    allergens: str = Form(""),
    description: str = Form(""),
    features: str = Form(""),
    table_setting: str = Form(""),
    gastronomic_pairings: str = Form(""),
    db: Session = Depends(get_db)
) -> Any:
    """Редактирование продукта"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к продукту
    check_product_access(current_user, product_id, db)
    
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_update = ProductUpdate(
        title=title,
        weight=weight if weight else None,
        ingredients=ingredients,
        allergens=allergens if allergens else None,
        description=description if description else None,
        features=features if features else None,
        table_setting=table_setting if table_setting else None,
        gastronomic_pairings=gastronomic_pairings if gastronomic_pairings else None
    )
    
    update_product(db, product_id, product_update)
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}/products/{product_id}", status_code=302)


@router.post("/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}/products/{product_id}/manage/delete", response_class=HTMLResponse)
async def delete_product_post(
    request: Request,
    restaurant_id: int,
    section_id: int,
    category_id: int,
    product_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Удаление продукта"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем доступ к продукту
    check_product_access(current_user, product_id, db)
    
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    category_id = int(getattr(product, 'category_id', -1))
    delete_product(db, product_id)
    
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section_id}/categories/{category_id}", status_code=302)


# === УПРАВЛЕНИЕ РЕСТОРАНАМИ ===

@router.get("/manage/restaurants/create", response_class=HTMLResponse)
async def create_restaurant_page(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Страница создания ресторана"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    return templates.TemplateResponse("manage/create_restaurant.html", {
        "request": request,
        "user": current_user
    })


@router.post("/manage/restaurants/create", response_class=HTMLResponse)
async def create_restaurant_post(
    request: Request,
    name: str = Form(...),
    concept: str = Form(""),
    db: Session = Depends(get_db)
) -> Any:
    """Создание ресторана"""
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    
    # Проверяем, есть ли уже ресторан у этого менеджера
    existing_restaurants = get_restaurants_by_manager(db, current_user.id)  # type: ignore
    if existing_restaurants:
        return templates.TemplateResponse(
            "manage/create_restaurant.html", 
            {
                "request": request, 
                "user": current_user,
                "error": "У вас уже есть ресторан. Каждый менеджер может управлять только одним рестораном."
            }
        )
    
    restaurant_data = RestaurantCreate(
        name=name,
        concept=concept if concept else None,
        manager_id=current_user.id  # type: ignore
    )
    
    create_restaurant(db, restaurant_data)
    return RedirectResponse(url="/restaurants", status_code=302)

@router.get("/restaurants/{restaurant_id}/manage/edit", response_class=HTMLResponse)
async def edit_restaurant_page(
    request: Request,
    restaurant_id: int,
    db: Session = Depends(get_db)
) -> Any:
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    check_restaurant_access(current_user, restaurant_id, db)
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return templates.TemplateResponse("manage/edit_restaurant.html", {
        "request": request,
        "user": current_user,
        "restaurant": restaurant
    })

@router.get("/manage/restaurants/edit/{restaurant_id}")
async def legacy_edit_restaurant_redirect(restaurant_id: int):
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/manage/edit", status_code=302)

@router.post("/restaurants/{restaurant_id}/manage/edit", response_class=HTMLResponse)
async def edit_restaurant_modal(
    request: Request,
    restaurant_id: int,
    name: str = Form(...),
    concept: str = Form(""),
    db: Session = Depends(get_db)
) -> Any:
    current_user = get_current_user_from_cookies(request, db)
    check_manager_access(current_user)
    check_restaurant_access(current_user, restaurant_id, db)
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    update_data = RestaurantCreate(name=name, concept=concept if concept else None)
    # Обновляем только name и concept
    setattr(restaurant, 'name', name)
    setattr(restaurant, 'concept', concept if concept else None)
    db.commit()
    db.refresh(restaurant)
    # После сохранения возвращаемся на detail ресторана
    return RedirectResponse(url=f"/restaurants/{restaurant_id}", status_code=302)

# --- REDIRECTS FROM OLD MANAGE ROUTES TO NEW NESTED ROUTES ---
@router.get("/manage/products/edit/{product_id}")
async def legacy_edit_product_redirect(product_id: int, db: Session = Depends(get_db)):
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    category_id = int(getattr(product, 'category_id', -1))
    category = get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    section_id = int(getattr(category, 'section_id', -1))
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    restaurant_id = int(getattr(product, 'restaurant_id', -1))
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section.id}/categories/{category.id}/products/{product.id}/manage/edit", status_code=302)

@router.get("/manage/products/create/{category_id}")
async def legacy_create_product_redirect(category_id: int, db: Session = Depends(get_db)):
    category = get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    section_id = int(getattr(category, 'section_id', -1))
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    restaurant_id = int(getattr(category, 'restaurant_id', -1))
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section.id}/categories/{category.id}/manage/products/create", status_code=302)

@router.post("/manage/products/delete/{product_id}")
async def legacy_delete_product_redirect(product_id: int, db: Session = Depends(get_db)):
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    category_id = int(getattr(product, 'category_id', -1))
    category = get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    section_id = int(getattr(category, 'section_id', -1))
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    restaurant_id = int(getattr(product, 'restaurant_id', -1))
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section.id}/categories/{category.id}/products/{product.id}/manage/delete", status_code=307)

# Аналогично для категорий и секций (edit/create/delete)
@router.get("/manage/categories/edit/{category_id}")
async def legacy_edit_category_redirect(category_id: int, db: Session = Depends(get_db)):
    category = get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    section_id = int(getattr(category, 'section_id', -1))
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    restaurant_id = int(getattr(category, 'restaurant_id', -1))
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section.id}/categories/{category.id}/manage/edit", status_code=302)

@router.get("/manage/categories/create/{section_id}")
async def legacy_create_category_redirect(section_id: int, db: Session = Depends(get_db)):
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    restaurant_id = int(getattr(section, 'restaurant_id', -1))
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section.id}/manage/categories/create", status_code=302)

@router.post("/manage/categories/delete/{category_id}")
async def legacy_delete_category_redirect(category_id: int, db: Session = Depends(get_db)):
    category = get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    section_id = int(getattr(category, 'section_id', -1))
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    restaurant_id = int(getattr(category, 'restaurant_id', -1))
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section.id}/categories/{category.id}/manage/delete", status_code=307)

@router.get("/manage/sections/edit/{section_id}")
async def legacy_edit_section_redirect(section_id: int, db: Session = Depends(get_db)):
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    restaurant_id = int(getattr(section, 'restaurant_id', -1))
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section.id}/manage/edit", status_code=302)

@router.get("/manage/sections/create/{restaurant_id}")
async def legacy_create_section_redirect(restaurant_id: int):
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/manage/sections/create", status_code=302)

@router.post("/manage/sections/delete/{section_id}")
async def legacy_delete_section_redirect(section_id: int, db: Session = Depends(get_db)):
    section = get_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    restaurant_id = int(getattr(section, 'restaurant_id', -1))
    return RedirectResponse(url=f"/restaurants/{restaurant_id}/sections/{section.id}/manage/delete", status_code=307)

async def custom_http_exception_handler(request: Request, exc: HTTPException):
    code = exc.status_code
    if code == 401:
        message = "Требуется авторизация для доступа к этой странице."
    elif code == 403:
        message = "У вас нет прав для доступа к этой странице."
    elif code == 404:
        message = "Страница не найдена или не существует."
    else:
        message = exc.detail or "Произошла неизвестная ошибка."
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error_code": code, "error_message": message},
        status_code=code
    )
import os
import aiohttp
import asyncio
import json
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("API_KEY")

ANIMALS_API_URL = "https://api.api-ninjas.com/v1/animals"
FACTS_API_URL = "https://api.api-ninjas.com/v1/facts"
ANIMAL_PARAMS = {"name": "tiger", "limit": 15}

REAL_TIGERS_DB = {
    "Бенгальский тигр": {
        "conservation": "Под угрозой (Endangered)",
        "fact": "Самый распространённый подвид тигра.",
        "weight": "180-258 кг",
        "habitat": "Индия, Бангладеш, Непал, Бутан",
        "family": "Кошачьи",
        "unique": "Могут съесть до 40 кг мяса за один приём!"
    },
    "Амурский тигр": {
        "conservation": "Вымирающий (Endangered)",
        "fact": "Самый крупный подвид тигра.",
        "weight": "180-306 кг", 
        "habitat": "Россия, Китай",
        "family": "Кошачьи",
        "unique": "Выдерживают морозы до -45°C!"
    },
    "Индокитайский тигр": {
        "conservation": "На грани исчезновения (Critically Endangered)",
        "fact": "Имеет более тёмный окрас, чем бенгальский тигр.",
        "weight": "150-195 кг",
        "habitat": "Таиланд, Мьянма, Лаос, Вьетнам, Камбоджа",
        "family": "Кошачьи",
        "unique": "Полосы уже и расположены чаще, чем у других подвидов"
    },
    "Малайский тигр": {
        "conservation": "На грани исчезновения (Critically Endangered)",
        "fact": "Самый маленький подвид на материковой Азии.",
        "weight": "100-130 кг",
        "habitat": "Малайзия, юг Таиланда",
        "family": "Кошачьи",
        "unique": "Признан отдельным подвидом только в 2004 году!"
    },
    "Суматранский тигр": {
        "conservation": "Критическая угроза (Critically Endangered)",
        "fact": "Самый маленький из ныне живущих подвидов.",
        "weight": "75-140 кг",
        "habitat": "Остров Суматра",
        "family": "Кошачьи",
        "unique": "Имеет самые тёмные полосы среди всех тигров!"
    },
    "Южнокитайский тигр": {
        "conservation": "Функционально вымерший (Possibly Extinct in Wild)",
        "fact": "Возможно уже вымер в дикой природе.",
        "weight": "130-175 кг",
        "habitat": "Исторически - Южный Китай",
        "family": "Кошачьи",
        "unique": "В неволе осталось около 100 особей"
    },
    "Белый тигр": {
        "conservation": "Не встречается в дикой природе",
        "fact": "Цветовая мутация бенгальского тигра.",
        "weight": "200-230 кг",
        "habitat": "Только в зоопарках",
        "family": "Кошачьи",
        "unique": "Встречается 1 на 10,000 особей"
    }
}

RUSSIAN_TIGER_FACTS = [
    "Тигры - самые крупные представители семейства кошачьих.",
    "Полосы каждого тигра уникальны, как отпечатки пальцев у человека.",
    "Тигр может прыгнуть на расстояние до 6 метров.",
    "Тигриный рык слышно на расстоянии до 3 километров.",
    "Тигры отличные пловцы и любят воду.",
    "Тигрята рождаются слепыми и полностью зависят от матери.",
    "Тигры обычно избегают людей и редко нападают первыми.",
    "В дикой природе тигры живут 10-15 лет.",
    "Тигры метят территорию мочой и царапинами на деревьях.",
    "Тигрицы вынашивают детёнышей около 3-4 месяцев."
]

NAME_TRANSLATION = {
    "Bengal Tiger": "Бенгальский тигр",
    "Siberian Tiger": "Амурский тигр",
    "Indochinese Tiger": "Индокитайский тигр",
    "Malayan Tiger": "Малайский тигр",
    "Sumatran Tiger": "Суматранский тигр",
    "South China Tiger": "Южнокитайский тигр",
    "White Tiger": "Белый тигр"
}

async def fetch_tiger_data(session: aiohttp.ClientSession) -> Tuple[List[Dict], List[str]]:
    try:
        async with session.get(
            ANIMALS_API_URL,
            headers={"X-Api-Key": API_KEY} if API_KEY else {},
            params=ANIMAL_PARAMS,
            timeout=aiohttp.ClientTimeout(10)
        ) as response:
            
            animals_data = []
            if response.status == 200:
                data = await response.json()
                animals_data = [
                    a for a in data 
                    if a.get("name") in NAME_TRANSLATION.keys()
                ]
            
        async with session.get(
            FACTS_API_URL,
            headers={"X-Api-Key": API_KEY} if API_KEY else {},
            params={"limit": 30},
            timeout=aiohttp.ClientTimeout(10)
        ) as response:
            
            facts = []
            if response.status == 200:
                data = await response.json()
                facts = [
                    f["fact"] for f in data 
                    if isinstance(f, dict) and 
                    "тигр" in f.get("fact", "").lower()
                ][:5]
            
        return animals_data, facts if facts else RUSSIAN_TIGER_FACTS[:5]
        
    except Exception as e:
        print(f"⚠️ Ошибка при запросе данных: {e}")
        return [], RUSSIAN_TIGER_FACTS[:5]

async def enhance_tiger_data(raw_animals: List[Dict], facts: List[str]) -> List[Dict]:
    enhanced = []
    used_facts = set()
    
    for animal in raw_animals:
        name = animal.get("name")
        if name not in NAME_TRANSLATION:
            continue
            
        name_ru = NAME_TRANSLATION[name]
        info = REAL_TIGERS_DB.get(name_ru, {})
        
        enhanced.append({
            "name": name_ru,
            "conservation": info.get("conservation", 
                animal.get("characteristics", {}).get("conservation_status", "Неизвестно")),
            "weight": info.get("weight", 
                animal.get("characteristics", {}).get("weight", "Неизвестно")),
            "habitat": info.get("habitat", 
                ", ".join(animal.get("locations", ["Неизвестно"]))),
            "family": info.get("family", 
                animal.get("taxonomy", {}).get("family", "Неизвестно")),
            "fact": info.get("fact", "Интересный факт отсутствует"),
            "unique": info.get("unique", "Нет дополнительной информации"),
            "random_fact": next((f for f in facts if f not in used_facts), None)
        })
        
        if enhanced[-1]["random_fact"]:
            used_facts.add(enhanced[-1]["random_fact"])
    
    api_names = {a["name"] for a in enhanced}
    for name_ru, info in REAL_TIGERS_DB.items():
        if name_ru not in api_names:
            enhanced.append({
                "name": name_ru,
                **info,
                "random_fact": next((f for f in facts if f not in used_facts), None)
            })
            if enhanced[-1]["random_fact"]:
                used_facts.add(enhanced[-1]["random_fact"])
    
    return enhanced

async def save_and_display(data: List[Dict]):
    save_dir = Path("data")
    save_dir.mkdir(exist_ok=True)
    filepath = save_dir / f"tigers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    
    print(f"\n{' ОТЧЕТ О ТИГРАХ ':=^60}")
    for tiger in data:
        print(f"\n🔹 {tiger['name']}")
        print(f"   🛡️ Статус сохранения: {tiger['conservation']}")
        print(f"   ⚖️ Вес: {tiger['weight']}")
        print(f"   🌍 Ареал обитания: {tiger['habitat']}")
        print(f"   🧬 Семейство: {tiger['family']}")
        print(f"   📌 Основной факт: {tiger['fact']}")
        if tiger.get('unique'):
            print(f"   🐾 Уникальная особенность: {tiger['unique']}")
        if tiger.get('random_fact'):
            print(f"   🔍 Случайный факт: {tiger['random_fact']}")
    
    print(f"\nДанные сохранены в: {filepath}")

async def main():
    print("\n🟢 Начинаем сбор информации о тиграх...")
    
    async with aiohttp.ClientSession() as session:
        raw_animals, facts = await fetch_tiger_data(session)
        enhanced_data = await enhance_tiger_data(raw_animals, facts)
        await save_and_display(enhanced_data)
    
    print("\n🔴 Работа программы завершена")

if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
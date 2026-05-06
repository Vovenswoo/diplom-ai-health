import json

class HealthSafetyAuditor:
    def __init__(self):
        self.contraindications_db = {
            "кифоз": ["осевая нагрузка", "прыжки", "становая тяга", "приседания со штангой", "скручивания"],
            "инсулинорезистентность": ["голодание", "высокоинтенсивный интервальный тренинг натощак"],
            "плоскостопие": ["бег по жесткой поверхности", "прыжки на скакалке"],
            "грыжа": ["осевая нагрузка", "становая тяга", "поднятие тяжестей", "скручивания"],
            "гипертония первой степени": ["задержка дыхания", "натуживание", "вниз головой", "тяжелые веса"],
            "варикоз": ["степ-аэробика", "прыжки", "глубокие приседания", "статическая нагрузка на ноги"]
        }

    def audit_plan(self, user_profile: dict, generated_plan: dict) -> dict:
        diseases = user_profile.get("illnesses", [])
        
        tasks_text = json.dumps(generated_plan.get("schedule", {}), ensure_ascii=False).lower()
        warnings_text = str(generated_plan.get("health_warnings", "")).lower()

        is_safe = True
        errors = []

        for disease in diseases:
            disease_lower = disease.lower()

            if disease_lower not in warnings_text:
                errors.append(f"Внимание: В поле 'health_warnings' не найдено явное упоминание заболевания '{disease}'")
                is_safe = False

            if disease_lower in self.contraindications_db:
                forbidden_words = self.contraindications_db[disease_lower]
                
                for word in forbidden_words:
                    if word in tasks_text:
                        errors.append(f"КРИТИЧЕСКАЯ ОШИБКА: Найдена запрещенная активность '{word}' при диагнозе '{disease}'")
                        is_safe = False

        return {
            "is_safe": is_safe,
            "errors": errors,
            "profile_diseases": diseases
        }

if __name__ == "__main__":
    test_user = {
        "age": "25",
        "illnesses": ["кифоз", "гипертония первой степени"]
    }

    bad_plan = {
        "health_warnings": ["Следите за пульсом из-за гипертонии."],
        "schedule": {
            "monday": [
                {"type": "strength", "focus": "приседания со штангой и осевая нагрузка"}
            ]
        }
    }

    print("--- Запуск Safety Audit ---")
    auditor = HealthSafetyAuditor()
    result = auditor.audit_plan(test_user, bad_plan)
    
    if result["is_safe"]:
        print("План абсолютно безопасен.")
    else:
        print("План не прошел проверку безопасности!")
        for err in result["errors"]:
            print(f" - {err}")
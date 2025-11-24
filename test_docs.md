# FastAPI
**Версия:** 0.1.0  
**Описание:** 



---

## 🚀 Эндпоинты


### `GET` /api/v1/notifications/{notificationId}
*Tag: notifications*


*ID операции:* `get_notification_detail_api_v1_notifications__notificationId__get`  

*Краткое описание:* Get Notification Detail  



**Требования безопасности:**

- **CustomAPIKeyHeader**


| Имя | Тип | Расположение | Обязательный | Описание |  Формат |
|-----|-----|--------------|--------------|----------|--------|
| `notificationId` | string | path | ✅ | Уникальный идентификатор уведомления (ObjectId)| |
#### Примеры параметров
**notificationId**

**Пример 1:** `68f8c56d5b847a388df4a4e0` 





##### Ответы  
###### **Код 200:** Successful Response

  - **Тип контента:** `application/json`  
    - **Схема:** [Notification](#notification)


###### **Код 401:** Пользователь не авторизован

  - **Тип контента:** `application/json`  

  - **Невалидный токен:**
    
```json
{
  "detail": "Ошибка декодирования токена."
}
```
  - **Не найден пользователь:**
    
```json
{
  "detail": "Сессия пользователя не была найдена."
}
```

###### **Код 403:** Доступ запрещен

  - **Тип контента:** `application/json`  

  - **У роли аккаунта недостаточно прав:**
    
```json
{
  "detail": "Доступ запрещён (недостаточно прав для роли)"
}
```
  - **Аккаунт не был выбран:**
    
```json
{
  "detail": "Доступ запрещён (не выбран аккаунт)"
}
```

###### **Код 404:** Not Found

  - **Тип контента:** `application/json`  

  - **Notification not found:**
    
```json
{
  "detail": "Notification not found"
}
```

###### **Код 422:** Validation Error

  - **Тип контента:** `application/json`  
    - **Схема:** [HTTPValidationError](#httpvalidationerror)




---

### `PUT` /api/v1/notifications/{notificationId}
*Tag: notifications*


*ID операции:* `update_notification_api_v1_notifications__notificationId__put`  

*Краткое описание:* Update Notification  



**Требования безопасности:**

- **CustomAPIKeyHeader**


| Имя | Тип | Расположение | Обязательный | Описание |  Формат |
|-----|-----|--------------|--------------|----------|--------|
| `notificationId` | string | path | ✅ | Уникальный идентификатор уведомления (ObjectId)| |
#### Примеры параметров
**notificationId**

**Пример 1:** `68f8c56d5b847a388df4a4df` 



**Тело запроса:**  

- **Тип контента:** `application/json`  
  - **Схема:** [NotificationRequest](#notificationrequest)

  **Свойства:**

  | Имя | Тип | Обязательный | Описание | Примеры | Формат |
  |-----|-----|--------------|----------|---------|--------|
  | `name` | object | ❌ | Name |  |  |
  | `type` | [NotificationType](#notificationtype) | ✅ | An enumeration. |  |  |
  | `details` | anyOf<[NotificationDetailTriggerRequest](#notificationdetailtriggerrequest) , [NotificationDetailSimpleRequest](#notificationdetailsimplerequest)> | ✅ | Details |  |  |
  | `teamIds` | array<string> | ✅ | Teamids |  |  |
  | `playerIds` | array<string> | ❌ | Playerids |  |  |
  | `coachIds` | array<string> | ❌ | Coachids |  |  |
  | `survey` | [api__v1__routes__notification__notifications__schemas__request__Survey](#api__v1__routes__notification__notifications__schemas__request__survey) | ✅ | Survey |  |  |
  | `isReminder` | boolean | ❌ | Isreminder |  |  |



##### Ответы  
###### **Код 204:** Successful Response

###### **Код 401:** Пользователь не авторизован

  - **Тип контента:** `application/json`  

  - **Невалидный токен:**
    
```json
{
  "detail": "Ошибка декодирования токена."
}
```
  - **Не найден пользователь:**
    
```json
{
  "detail": "Сессия пользователя не была найдена."
}
```

###### **Код 403:** Доступ запрещен

  - **Тип контента:** `application/json`  

  - **У роли аккаунта недостаточно прав:**
    
```json
{
  "detail": "Доступ запрещён (недостаточно прав для роли)"
}
```
  - **Аккаунт не был выбран:**
    
```json
{
  "detail": "Доступ запрещён (не выбран аккаунт)"
}
```

###### **Код 404:** Not Found

  - **Тип контента:** `application/json`  

  - **Notification not found:**
    
```json
{
  "detail": "Notification not found"
}
```

###### **Код 422:** Validation Error

  - **Тип контента:** `application/json`  
    - **Схема:** [HTTPValidationError](#httpvalidationerror)




---

## 📖 Схемы данных
### HTTPValidationError
 - **Название:** HTTPValidationError
 - **Тип:** `object`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `detail` | array<[ValidationError](#validationerror)> | ❌ | Detail  |  |

#### Примеры параметров

**detail:**
⚠️ *Пример отсутсвует*



### Notification
 - **Название:** Notification
 - **Тип:** `object`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `id` | string | ❌ | Id  |  |
| `name` | string | ❌ | Name  |  |
| `type` | [NotificationType](#notificationtype) | ❌ | An enumeration.  |  |
| `isReminder` | boolean | ❌ | Isreminder  |  |
| `details` | anyOf<[NotificationDetailSimple](#notificationdetailsimple) , [NotificationDetailTrigger](#notificationdetailtrigger)> | ❌ | Details  |  |
| `players` | array<[NotificationPlayer](#notificationplayer)> | ❌ | Players  |  |
| `teams` | array<[NotificationTeams](#notificationteams)> | ❌ | Teams  |  |
| `coaches` | array<[NotificationCoaches](#notificationcoaches)> | ❌ | Coaches  |  |
| `survey` | [api__v1__routes__notification__notifications__schemas__response__Survey](#api__v1__routes__notification__notifications__schemas__response__survey) | ❌ | Survey  |  |

#### Примеры параметров

**id:**

**Пример:** `68f8cb775b847a388df4a4f9`




**name:**
⚠️ *Пример отсутсвует*




**type:**
⚠️ *Пример отсутсвует*




**isReminder:**
⚠️ *Пример отсутсвует*




**details:**
⚠️ *Пример отсутсвует*




**players:**
⚠️ *Пример отсутсвует*




**teams:**
⚠️ *Пример отсутсвует*




**coaches:**
⚠️ *Пример отсутсвует*




**survey:**
⚠️ *Пример отсутсвует*



### NotificationCoaches
 - **Название:** NotificationCoaches
 - **Тип:** `object`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `id` | string | ❌ | Id  |  |
| `name` | string | ❌ | Name  |  |

#### Примеры параметров

**id:**

**Пример:** `ca59d80d-90c5-4ee6-b371-d7822d8b24bb`




**name:**
⚠️ *Пример отсутсвует*



### NotificationDetailSimple
 - **Название:** NotificationDetailSimple
 - **Тип:** `object`
 - **Обязательные поля:** `periodicType`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `bringDatetime` | string | ❌ | Bringdatetime  | date-time |
| `periodicType` | [PeriodicyType](#periodicytype) | ✅ | An enumeration.  |  |

#### Примеры параметров

**bringDatetime:**

**Пример:** `2025-10-22T12:17:59+00:00`




**periodicType:**
⚠️ *Пример отсутсвует*



### NotificationDetailSimpleRequest
 - **Название:** NotificationDetailSimpleRequest
 - **Тип:** `object`
 - **Обязательные поля:** `bringDatetime, periodicType`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `bringDatetime` | string | ✅ | Bringdatetime  | date-time |
| `periodicType` | [PeriodicyType](#periodicytype) | ✅ | An enumeration.  |  |

#### Примеры параметров

**bringDatetime:**

**Пример:** `2025-10-22T12:17:59+00:00`




**periodicType:**
⚠️ *Пример отсутсвует*



### NotificationDetailTrigger
 - **Название:** NotificationDetailTrigger
 - **Тип:** `object`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `bringDatetime` | string | ❌ | Bringdatetime  | date-time |
| `triggerId` | string | ❌ | Triggerid  |  |

#### Примеры параметров

**bringDatetime:**

**Пример:** `2025-10-22T12:17:59+00:00`




**triggerId:**

**Пример:** `68f8cb775b847a388df4a501`



### NotificationDetailTriggerRequest
 - **Название:** NotificationDetailTriggerRequest
 - **Тип:** `object`
 - **Обязательные поля:** `bringDatetime, triggerId`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `bringDatetime` | string | ✅ | Bringdatetime  | date-time |
| `triggerId` | string | ✅ | Triggerid  |  |

#### Примеры параметров

**bringDatetime:**

**Пример:** `2025-10-22T12:17:59+00:00`




**triggerId:**

**Пример:** `68f8cb775b847a388df4a503`



### NotificationPlayer
 - **Название:** NotificationPlayer
 - **Тип:** `object`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `id` | string | ❌ | Id  |  |
| `name` | string | ❌ | Name  |  |

#### Примеры параметров

**id:**

**Пример:** `4c373afd-9602-4e6e-b578-f2eb923c2bdd`




**name:**
⚠️ *Пример отсутсвует*



### NotificationRequest
 - **Название:** NotificationRequest
 - **Тип:** `object`
 - **Обязательные поля:** `type, details, teamIds, survey`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `name` | object | ❌ | Name  |  |
| `type` | [NotificationType](#notificationtype) | ✅ | An enumeration.  |  |
| `details` | anyOf<[NotificationDetailTriggerRequest](#notificationdetailtriggerrequest) , [NotificationDetailSimpleRequest](#notificationdetailsimplerequest)> | ✅ | Details  |  |
| `teamIds` | array<string> | ✅ | Teamids  |  |
| `playerIds` | array<string> | ❌ | Playerids  |  |
| `coachIds` | array<string> | ❌ | Coachids  |  |
| `survey` | [api__v1__routes__notification__notifications__schemas__request__Survey](#api__v1__routes__notification__notifications__schemas__request__survey) | ✅ | Survey  |  |
| `isReminder` | boolean | ❌ | Isreminder  |  |

#### Примеры параметров

**name:**
⚠️ *Пример отсутсвует*




**type:**
⚠️ *Пример отсутсвует*




**details:**
⚠️ *Пример отсутсвует*




**teamIds:**
⚠️ *Пример отсутсвует*




**playerIds:**
⚠️ *Пример отсутсвует*




**coachIds:**
⚠️ *Пример отсутсвует*




**survey:**
⚠️ *Пример отсутсвует*




**isReminder:**
⚠️ *Пример отсутсвует*



**Пример:**  
```json
{
  "coachIds": [
    "550e8400-e29b-41d4-a716-446655440333"
  ],
  "details": {
    "bringDatetime": "2023-10-01T10:00:00Z",
    "triggerId": "6512bd43d9caa6e02c990b0a"
  },
  "isReminder": true,
  "name": "\u0423\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435 \u043e \u0442\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u043a\u0435 \u043a\u043e\u043c\u0430\u043d\u0434\u044b",
  "survey": {
    "questions": [
      {
        "options": [
          "\u041e\u0442\u043b\u0438\u0447\u043d\u043e",
          "\u0425\u043e\u0440\u043e\u0448\u043e",
          "\u0423\u0434\u043e\u0432\u043b\u0435\u0442\u0432\u043e\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u043e",
          "\u041f\u043b\u043e\u0445\u043e"
        ],
        "text": "\u041a\u0430\u043a \u0432\u044b \u043e\u0446\u0435\u043d\u0438\u0432\u0430\u0435\u0442\u0435 \u0441\u0435\u0433\u043e\u0434\u043d\u044f\u0448\u043d\u044e\u044e \u0442\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u043a\u0443?",
        "type": "selectively"
      },
      {
        "options": [],
        "text": "\u0415\u0441\u0442\u044c \u043b\u0438 \u0443 \u0432\u0430\u0441 \u0442\u0440\u0430\u0432\u043c\u044b?",
        "type": "arbitrary"
      }
    ],
    "text": "\u0410\u043d\u043a\u0435\u0442\u0430 \u043f\u043e\u0441\u043b\u0435 \u0442\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u043a\u0438"
  },
  "teamIds": [
    "550e8400-e29b-41d4-a716-446655440000"
  ],
  "type": "trigger"
}
```
### NotificationTeams
 - **Название:** NotificationTeams
 - **Тип:** `object`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `id` | string | ❌ | Id  |  |
| `name` | string | ❌ | Name  |  |

#### Примеры параметров

**id:**

**Пример:** `59e071f8-8439-45fa-b91f-d9d750206557`




**name:**
⚠️ *Пример отсутсвует*



### NotificationType
 - **Название:** NotificationType
 - **Тип:** `string`
 - **Описание:** An enumeration.


#### Примеры параметров
### PeriodicyType
 - **Название:** PeriodicyType
 - **Тип:** `string`
 - **Описание:** An enumeration.


#### Примеры параметров
### QuestionType
 - **Название:** QuestionType
 - **Тип:** `string`
 - **Описание:** An enumeration.


#### Примеры параметров
### ValidationError
 - **Название:** ValidationError
 - **Тип:** `object`
 - **Обязательные поля:** `loc, msg, type`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `loc` | array<anyOf<string , integer>> | ✅ | Location  |  |
| `msg` | string | ✅ | Message  |  |
| `type` | string | ✅ | Error Type  |  |

#### Примеры параметров

**loc:**
⚠️ *Пример отсутсвует*




**msg:**
⚠️ *Пример отсутсвует*




**type:**
⚠️ *Пример отсутсвует*



### api__v1__routes__notification__notifications__schemas__request__Survey
 - **Название:** Survey
 - **Тип:** `object`
 - **Обязательные поля:** `text, questions`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `text` | string | ✅ | Text  |  |
| `questions` | array<[api__v1__routes__notification__notifications__schemas__request__SurveyQuestion](#api__v1__routes__notification__notifications__schemas__request__surveyquestion)> | ✅ | Questions  |  |

#### Примеры параметров

**text:**
⚠️ *Пример отсутсвует*




**questions:**
⚠️ *Пример отсутсвует*



### api__v1__routes__notification__notifications__schemas__request__SurveyQuestion
 - **Название:** SurveyQuestion
 - **Тип:** `object`
 - **Обязательные поля:** `type, text, options`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `type` | [QuestionType](#questiontype) | ✅ | An enumeration.  |  |
| `text` | string | ✅ | Text  |  |
| `options` | array<string> | ✅ | Options  |  |

#### Примеры параметров

**type:**
⚠️ *Пример отсутсвует*




**text:**
⚠️ *Пример отсутсвует*




**options:**
⚠️ *Пример отсутсвует*



### api__v1__routes__notification__notifications__schemas__response__Survey
 - **Название:** Survey
 - **Тип:** `object`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `id` | string | ❌ | Id  |  |
| `text` | string | ❌ | Text  |  |
| `questions` | array<[api__v1__routes__notification__notifications__schemas__response__SurveyQuestion](#api__v1__routes__notification__notifications__schemas__response__surveyquestion)> | ❌ | Questions  |  |

#### Примеры параметров

**id:**

**Пример:** `68f8cb775b847a388df4a4fd`




**text:**
⚠️ *Пример отсутсвует*




**questions:**
⚠️ *Пример отсутсвует*



### api__v1__routes__notification__notifications__schemas__response__SurveyQuestion
 - **Название:** SurveyQuestion
 - **Тип:** `object`

#### **Свойства:**

| Имя | Тип | Обязательный | Описание |  Формат |
|-----|-----|--------------|----------|--------|
| `type` | [QuestionType](#questiontype) | ❌ | An enumeration.  |  |
| `text` | string | ❌ | Text  |  |
| `options` | array<string> | ❌ | Options  |  |

#### Примеры параметров

**type:**
⚠️ *Пример отсутсвует*




**text:**
⚠️ *Пример отсутсвует*




**options:**
⚠️ *Пример отсутсвует*




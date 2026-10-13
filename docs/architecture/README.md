# KOYASH Architecture

Project: KOYASH  
Team: Sunwise  
Increment: MVP v2 (Sprint 3)

This document describes the KOYASH architecture using three views — static,
dynamic, and deployment — as diagrams-as-code (PlantUML). The diagram sources live
next to this file and are embedded below.

## System overview

KOYASH is a skincare recommendation web application. A single-page application (SPA)
built with React and Vite is served by nginx, which also reverse-proxies API calls to
a FastAPI backend. The backend applies rule-based recommendation logic over a product
catalogue stored in MongoDB.

The whole system runs as three Docker containers behind one public port, which keeps
deployment and access on the university VM simple and avoids cross-origin (CORS)
complexity.

## Static view

The static view shows the main components and their dependencies. The backend is
organized in layers: thin API endpoints delegate to services, services orchestrate
pure-function algorithms and repositories, and repositories isolate MongoDB access.

@startuml koyash-component-view

title KOYASH — Static Component View (MVP v2)

skinparam componentStyle rectangle

actor "User (browser)" as user

package "Frontend container (nginx)" {

[React + Vite SPA] as spa

[nginx (static + reverse proxy)] as nginx

}

package "Backend container (FastAPI / uvicorn)" {

[API layer (routers & endpoints)] as api

[Service layer] as services

[Recommendation algorithms (filter / score / sort / routine)] as algo

[Repository layer] as repos

[Core (config, security, enums)] as core

[Pydantic schemas] as schemas

}

database "MongoDB" as mongo

user --> nginx : HTTP :8080

nginx --> spa : serve static build

nginx --> api : proxy /api/v1/* (:8000)

api --> services

services --> algo

services --> repos

repos --> mongo

api ..> schemas

services ..> core

@enduml

Source: [`static-view/component-view.puml`](static-view/component-view.puml)

## Dynamic view

The dynamic view shows the main recommendation flow: the user completes the
questionnaire, the SPA calls the API through nginx, the service loads products,
applies the recommendation algorithms, builds explanations, persists the result, and
returns the routine.

@startuml koyash-recommendation-sequence

title KOYASH — Recommendation Flow (Dynamic View)

actor User

participant "SPA (browser)" as SPA

participant "nginx" as NGINX

participant "recommendations endpoint" as API

participant "RecommendationService" as SVC

participant "ProductRepository" as REPO

database "MongoDB" as DB

participant "Algorithms" as ALGO

participant "ExplanationService" as EXP

participant "RecommendationRepository" as RREPO

User -> SPA : complete questionnaire

SPA -> NGINX : POST /api/v1/recommendations

NGINX -> API : proxy POST /recommendations

API -> SVC : create_recommendation(request)

SVC -> REPO : list_active_products()

REPO -> DB : query active products

DB --> REPO : products

REPO --> SVC : products

SVC -> ALGO : filter -> score -> sort -> build routine

ALGO --> SVC : routine

SVC -> EXP : build explanations

EXP --> SVC : explanations

SVC -> RREPO : save recommendation

RREPO -> DB : insert

SVC --> API : RecommendationResponse

API --> NGINX : 200 JSON

NGINX --> SPA : 200 JSON

SPA --> User : show cosmetic bag + explanations

@enduml

Source: [`dynamic-view/recommendation-sequence.puml`](dynamic-view/recommendation-sequence.puml)

## Deployment view

The deployment view shows the runtime topology on the university VM: three containers
on one Docker bridge network, a persistent volume for MongoDB, and a single public
entry point on port 8080.

@startuml koyash-deployment-view

title KOYASH — Deployment View (MVP v2)

node "University VM (10.93.26.208)" as vm {

node "Docker Engine" as docker {

node "koyash-frontend (nginx:1.27) port 8080 -> 80" as fe {

[SPA static build]

}

node "koyash-backend (python:3.12 / uvicorn) port 8000" as be {

[FastAPI app]

}

node "koyash-mongo (mongo:7) port 27017" as db {

[MongoDB]

}

database "koyash_mongo_data (volume)" as vol

}

}

actor "User / Customer / TA" as user

user --> fe : http://10.93.26.208:8080/

fe --> be : /api -> backend:8000 (koyash-network)

be --> db : mongodb (koyash-network)

db --> vol : persist data

@enduml

Source: [`deployment-view/deployment.puml`](deployment-view/deployment.puml)

## Quality attributes

- **Cohesion:** each backend layer has a single responsibility — endpoints handle
  HTTP, services hold business logic, repositories handle persistence, and algorithms
  are pure functions. This keeps modules focused and readable.
- **Coupling:** layers depend inward through explicit dependency injection
  (FastAPI `Depends`). Endpoints do not touch MongoDB directly, so storage details are
  isolated behind repositories.
- **Maintainability:** pure-function algorithms and thin endpoints are easy to unit
  test; the same-origin nginx setup removes CORS configuration as a source of
  environment-specific bugs.
- **Deployability:** the system is fully containerized and starts with a single
  `docker compose up -d --build`; data is seeded automatically on startup.

## Mapping to quality requirements

| View / decision | Supported quality requirement |
|---|---|
| Single-port nginx reverse-proxy (deployment) | QR-02 (availability), QR-03 (operability) |
| MongoDB product catalogue (static) | QR-01 (recommendation data correctness) |
| Layered backend (static) | QR-01 (correctness), maintainability |
| Startup data seeding (deployment) | QR-02 (main flow available right after deploy) |

Architecture decisions are recorded in [`adr/`](adr/).

## Rendering the diagrams

Diagram sources are PlantUML. They render automatically on GitLab instances with the
PlantUML integration enabled (the embedded plantuml blocks above). To render locally:

plantuml docs/architecture/**/*.puml
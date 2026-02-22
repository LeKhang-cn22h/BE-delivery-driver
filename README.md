<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=700&size=32&pause=1000&color=2496ED&center=true&vCenter=true&width=600&lines=BE+Delivery+Driver;Microservice+Backend+System;Smart+Routing+%26+Scheduling" alt="Typing SVG" />
</p>

<p align="center">
  <strong>System Delivery Driver</strong> is a delivery management platform consisting of three components:<br/>
  a mobile application for drivers, a web dashboard for admins and customers,<br/>
  and a backend microservice handling all business logic.<br/><br/>
  <strong>This repository</strong> is the backend — comprising <strong>6 microservices</strong> responsible for:
</p>

<div align="center">

| Responsibility |
|:---|
Receiving and automatically assigning delivery orders to drivers |
Optimizing delivery routes using OSRM |
Smart scheduling and order assignment via Genetic Algorithm |
Real-time driver location tracking via WebSocket |
Instant push notifications to drivers and customers via Firebase |
Suggesting optimized pickup & delivery groupings via Association Rule Mining |

</div>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" />
  <img src="https://img.shields.io/badge/Kafka-231F20?style=for-the-badge&logo=apachekafka&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
  <img src="https://img.shields.io/badge/python-3.11-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/microservices-6-orange?style=flat-square" />
</p>

---

##  Table of Contents

- [Business Problem](#-business-problem)
- [Architecture](#️-architecture)
- [Tech Stack](#️-tech-stack)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Related Repositories](#-related-repositories)
- [Team](#-team)
- [Learning](#-learning)

---

##  Business Problem

Delivery companies in Vietnam currently lack effective two-way communication with customers, making it difficult for senders and recipients to track their orders in detail — similar to the limitations seen in services like Viettel Post and Vietnam Post. Drivers rely on experience and intuition when planning routes, which creates challenges for new drivers and makes order handover inefficient. Additionally, valuable data on pickup and delivery points goes unused, missing opportunities for business insights.

**Current Pain Points:**
-  Customers have limited visibility into real-time order status and estimated delivery times
-  Drivers plan routes manually based on intuition, leading to inefficient and longer delivery paths
-  Order assignment is done manually, causing delays and errors especially for new drivers
-  No mechanism for reassigning orders when drivers encounter issues
- Pickup and delivery data is collected but never analyzed for business value

**How This System Solves It:**
-  Customers can track their orders in real-time with detailed status updates via WebSocket and push notifications
-  Delivery routes are automatically optimized using OSRM to find the shortest and most efficient path
-  Orders are intelligently scheduled and assigned to drivers using a Genetic Algorithm
-  Orders can be reassigned to another driver when unexpected issues occur
-  Association Rule Mining analyzes pickup and delivery point patterns to suggest business expansion opportunities such as new service locations or partner stores

---

##  Architecture

The system is built on a **Microservice Architecture** with event-driven communication between services:

```
┌──────────────────────────────────────────────────────┐
│                     API Gateway                       │
└───┬──────────┬──────────┬──────────┬─────────────────┘
    │          │          │          │
┌───▼──┐  ┌───▼──┐  ┌────▼───┐  ┌───▼──────────┐
│Admin │  │Recv  │  │Sched   │  │Routing       │
│Orders│  │Orders│  │Service │  │Service       │
└───┬──┘  └───┬──┘  └────────┘  └──────────────┘
    │          │
┌───▼──────────▼────────────────────────────────┐
│           Apache Kafka / RabbitMQ              │
└───┬────────────────────────┬──────────────────┘
    │                        │
┌───▼──────────┐      ┌──────▼──────┐
│ Notification │      │  WebSocket  │
│  Service     │      │  Service    │
└──────────────┘      └─────────────┘
         │
┌────────▼──────────────────────────────────────┐
│              Supabase (PostgreSQL)             │
└───────────────────────────────────────────────┘
```

<!-- Replace with Draw.io diagram if available: ![Architecture](./docs/architecture.png) -->

---

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Language | Python |
| Framework | FastAPI |
| Database | Supabase (PostgreSQL) |
| Message Broker | Apache Kafka, RabbitMQ |
| Real-time | WebSocket |
| Push Notification | Firebase Cloud Messaging (FCM) |
| Route Optimization | OSRM (Open Source Routing Machine) |
| Scheduling Algorithm | Genetic Algorithm |
| Data Mining | Association Rule Mining (Apriori) |
| Data Lake / Object Storage | MinIO |
| Business Intelligence | Metabase |
| Containerization | Docker, Docker Compose |
| Template Engine | Cookiecutter |

<p>
  <img src="https://skillicons.dev/icons?i=python,fastapi,supabase,docker,firebase,kafka" />
</p>
<p>
  <img src="https://img.shields.io/badge/MinIO-C72E49?style=for-the-badge&logo=minio&logoColor=white" />
  <img src="https://img.shields.io/badge/Metabase-509EE3?style=for-the-badge&logo=metabase&logoColor=white" />
</p>

##  Features

** Authentication**
- Shared login and registration for Admin and Customer
- Role-based access control — redirects to the appropriate dashboard based on user role

** Admin**
- Manage delivery orders (create, update, track status)
- Manage driver schedules with Genetic Algorithm auto-scheduling
- Manage drivers (profiles, assignment, performance)
- Manage post offices and service locations
- View Association Rule Mining results and business expansion suggestions
- Receive real-time notifications
- Manage account profile

**Customer**
- Create and manage delivery orders
- Track real-time order status with detailed updates
- View delivery statistics dashboard
- Manage saved delivery addresses
- Receive push notifications on order status changes
- Manage account profile

**System**
- Automated order receiving and driver assignment
- Delivery route optimization with OSRM
- Intelligent order scheduling via Genetic Algorithm
- Order reassignment to another driver when issues occur
- Real-time driver location tracking via WebSocket
- Instant push notifications via Firebase Cloud Messaging
- Business insights via Association Rule Mining on pickup/delivery data
- Full system deployment with Docker Compose

---

## Project Structure

```
BE-delivery-driver/
├── backend/
│   ├── services/
│   │   ├── manager_orders/         # Admin order management (orders, drivers, post offices)
│   │   │   └── app/
│   │   │       ├── infrastructure/
│   │   │       │   ├── database/   # Supabase repositories (order, driver, post_office)
│   │   │       │   └── events/     # Kafka event publisher
│   │   │       └── presentation/
│   │   │           └── api/        # Routes: order, driver, post_office, pickup_schedule
│   │   │
│   │   ├── receive_orders/         # Receives and processes incoming orders
│   │   │   └── app/
│   │   │       ├── application/
│   │   │       │   ├── consumers/  # Kafka order consumer
│   │   │       │   └── services/   # Driver workflow service
│   │   │       └── infrastructure/
│   │   │           ├── messaging/  # Kafka producer
│   │   │           └── supabase/   # Driver workflow repository
│   │   │
│   │   ├── routing-service/        # Delivery route optimization
│   │   │   └── app/
│   │   │       ├── services/       # OSRM service, distance matrix, optimizer
│   │   │       └── api/v1/         # Route optimization endpoints
│   │   │
│   │   ├── scheduler_service/      # Driver scheduling and order assignment
│   │   │   └── app/
│   │   │       ├── domain/
│   │   │       │   └── services/   # Genetic Algorithm scheduler
│   │   │       └── application/
│   │   │           └── use_cases/  # Create, get, update schedule
│   │   │
│   │   ├── notification/           # Push notifications to drivers and customers
│   │   │   └── app/
│   │   │       ├── infrastructure/
│   │   │       │   └── messaging/  # Kafka consumer & producer
│   │   │       └── application/    # Notification use cases & services
│   │   │
│   │   └── WebSocket/              # Real-time driver location tracking
│   │       └── app/
│   │           ├── ws/             # Connection manager, location routes
│   │           └── services/       # Location service
│   │
│   ├── shared/                     # Shared modules across services
│   │   ├── auth/                   # JWT, permissions, dependencies
│   │   ├── logging/                # Logger configuration
│   │   ├── schemas/                # Base schemas, pagination, response
│   │   └── utils/                  # Helpers, ID, time utilities
│   │
│   └── templates/
│       └── microservice-template/  # Cookiecutter template for new services
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Git

###  Run with Docker Hub *(recommended — no need to clone the source code)*

```bash
# Step 1 — Download docker-compose file
curl -O https://raw.githubusercontent.com/LeKhang-cn22h/BE-delivery-driver/main/docker-compose.yml

# Step 2 — Set up environment variables
curl -O https://raw.githubusercontent.com/LeKhang-cn22h/BE-delivery-driver/main/.env.example
cp .env.example .env
# Open .env and fill in the required values

# Step 3 — Pull images and start all services
docker-compose up -d
```

> Docker Hub images: [hub.docker.com/r/lekhang/be-delivery-driver](https://hub.docker.com/r/lekhang/be-delivery-driver)

###  Run from Source

```bash
# Clone the repository
git clone https://github.com/LeKhang-cn22h/BE-delivery-driver.git
cd BE-delivery-driver

# Set up environment variables
cp .env.example .env

# Start all services
docker-compose up -d
```
## Related Repositories

| Repository | Description | Link |
|------------|-------------|------|
|  Mobile App | Flutter mobile application for drivers | [FE-mobile-delivery-driver](https://github.com/LeKhang-cn22h/FE-mobile-delivery-driver) |
|  Web App | Web dashboard for admins and customers | [DeliveryDriver-Web](https://github.com/hohuynhnhu/DeliveryDriver-Web) |
|  Docker Hub | Container images | [hub.docker.com/r/lekhang/be-delivery](https://hub.docker.com/r/lekhang/be-delivery) |

---

##  Team

| Name | Role | GitHub |
|------|------|--------|
| Lê Tuấn Khang | Team Lead & Backend Developer | [@LeKhang-cn22h](https://github.com/LeKhang-cn22h) |
| Hồ Huỳnh Nhu | Backend Developer | [@hohuynhnhu](https://github.com/hohuynhnhu) |

---

## Learning

Knowledge and skills gained throughout this project:

**Architecture & Design**
- Designing and implementing a real-world Microservice architecture
- Applying Clean Architecture within each service (domain, application, infrastructure, presentation layers)
- Building an Event-driven system using Apache Kafka and RabbitMQ

**Backend Development**
- Building RESTful APIs with FastAPI
- Working with Supabase (PostgreSQL) as a backend-as-a-service
- Implementing WebSocket for real-time driver location tracking
- Integrating Firebase Cloud Messaging (FCM) for push notifications

**Algorithms & Data**
- Implementing Genetic Algorithm for intelligent driver scheduling and order assignment
- Route optimization using OSRM and distance matrix computation
- Applying Association Rule Mining (Apriori) to analyze pickup and delivery point patterns

**DevOps**
- Containerizing each microservice with Docker
- Configuring Docker Compose for a multi-service system
- Managing environment variables and service secrets with `.env`
- Publishing container images to Docker Hub

---

## License

MIT License © 2026

# Voice Agent Orchestrator - System Architecture

## 🏗️ High-Level System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           VOICE AGENT ORCHESTRATOR                              │
│                              Production System                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLIENT APPS   │    │   WEB BROWSER   │    │   MOBILE APPS   │
│                 │    │                 │    │                 │
│ • React Native  │    │ • React/Vue     │    │ • iOS/Android   │
│ • Flutter       │    │ • Angular       │    │ • Cross-platform│
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      NGINX REVERSE        │
                    │         PROXY             │
                    │                           │
                    │ • SSL Termination         │
                    │ • Load Balancing          │
                    │ • Rate Limiting           │
                    │ • Security Headers        │
                    │ • CORS Management         │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │     API GATEWAY           │
                    │                           │
                    │ • Authentication          │
                    │ • Authorization           │
                    │ • Request Routing         │
                    │ • Response Aggregation    │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────▼─────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│  NODE.JS REALTIME │    │ PYTHON ORCHESTRATOR │    │   MONITORING   │
│     BACKEND       │    │     BACKEND         │    │   SERVICES     │
│                   │    │                     │    │                │
│ • WebSocket       │    │ • LangChain         │    │ • Prometheus   │
│ • Voice Handling  │    │ • Intent Processing │    │ • Grafana      │
│ • Real-time       │    │ • AI/LLM            │    │ • Health Checks│
│ • Session Mgmt    │    │ • Conversation      │    │ • Metrics      │
└─────────┬─────────┘    │   Management        │    └────────────────┘
          │              └─────────┬───────────┘
          │                        │
          └────────────────────────┼────────────────────────┐
                                   │                        │
                    ┌──────────────▼──────────────┐         │
                    │      VOICE PROVIDERS        │         │
                    │                             │         │
                    │ ┌─────────┐ ┌─────────┐    │         │
                    │ │ SARVAM  │ │ TWILIO  │    │         │
                    │ │   AI    │ │         │    │         │
                    │ └─────────┘ └─────────┘    │         │
                    │ ┌─────────┐ ┌─────────┐    │         │
                    │ │ VONAGE  │ │ AWS     │    │         │
                    │ │         │ │ CONNECT │    │         │
                    │ └─────────┘ └─────────┘    │         │
                    └─────────────────────────────┘         │
                                   │                        │
                    ┌──────────────▼──────────────┐         │
                    │      DATA LAYER             │         │
                    │                             │         │
                    │ ┌─────────┐ ┌─────────┐    │         │
                    │ │ AZURE   │ │ REDIS   │    │         │
                    │ │POSTGRES │ │ CACHE   │    │         │
                    │ └─────────┘ └─────────┘    │         │
                    │ ┌─────────┐ ┌─────────┐    │         │
                    │ │ AZURE   │ │ CHROMA  │    │         │
                    │ │  BLOB   │ │   DB    │    │         │
                    │ └─────────┘ └─────────┘    │         │
                    └─────────────────────────────┘         │
                                   │                        │
                    ┌──────────────▼──────────────┐         │
                    │      AI/LLM SERVICES        │         │
                    │                             │         │
                    │ ┌─────────┐ ┌─────────┐    │         │
                    │ │ AZURE   │ │ OPENAI  │    │         │
                    │ │ OPENAI  │ │   API   │    │         │
                    │ └─────────┘ └─────────┘    │         │
                    └─────────────────────────────┘         │
                                                            │
                    ┌───────────────────────────────────────▼──────────────┐
                    │              SECURITY & AUTHENTICATION               │
                    │                                                     │
                    │ • JWT Tokens                                        │
                    │ • Azure AD B2C                                      │
                    │ • API Key Management                                │
                    │ • Rate Limiting                                     │
                    │ • Input Validation                                  │
                    │ • CORS Protection                                   │
                    └─────────────────────────────────────────────────────┘
```

## 🔄 Request Flow Architecture

```
1. CLIENT REQUEST
   ┌─────────────┐
   │   Client    │ ──┐
   │ Application │   │
   └─────────────┘   │
                     │ HTTP/WebSocket
                     ▼
   ┌─────────────────┐
   │   Nginx Proxy   │ ──┐
   │                 │   │
   │ • SSL/TLS       │   │
   │ • Rate Limiting │   │
   │ • Load Balance  │   │
   └─────────────────┘   │
                         │
                         ▼
   ┌─────────────────┐
   │  Node.js        │ ──┐
   │  Realtime       │   │
   │  Backend        │   │
   └─────────────────┘   │
                         │
                         ▼
   ┌─────────────────┐
   │  Python         │ ──┐
   │  Orchestrator   │   │
   │  Backend        │   │
   └─────────────────┘   │
                         │
                         ▼
   ┌─────────────────┐
   │  Voice Provider │ ──┐
   │  (Sarvam AI)    │   │
   └─────────────────┘   │
                         │
                         ▼
   ┌─────────────────┐
   │  AI/LLM         │
   │  Services       │
   └─────────────────┘
```

## 🎯 Voice Interaction Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOICE INTERACTION FLOW                      │
└─────────────────────────────────────────────────────────────────┘

1. INCOMING CALL
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │   User      │───▶│ Sarvam AI   │───▶│ Node.js     │
   │  Calls      │    │   Voice     │    │ Realtime    │
   │  System     │    │  Provider   │    │ Backend     │
   └─────────────┘    └─────────────┘    └─────────────┘
                                │
                                ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ Python      │◀───│ WebSocket   │◀───│ Voice      │
   │ Orchestrator│    │ Connection  │    │ Processing │
   │ Backend     │    │             │    │            │
   └─────────────┘    └─────────────┘    └─────────────┘
          │
          ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ LangChain   │───▶│ Intent      │───▶│ Response    │
   │ Processing  │    │ Detection   │    │ Generation  │
   └─────────────┘    └─────────────┘    └─────────────┘
          │
          ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ TTS         │───▶│ Audio       │───▶│ User        │
   │ Generation  │    │ Response    │    │ Hears       │
   └─────────────┘    └─────────────┘    └─────────────┘
```

## 🗄️ Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA FLOW LAYER                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Node.js   │───▶│    Redis    │◀───│   Python    │
│  Realtime   │    │    Cache    │    │Orchestrator │
│  Backend    │    │             │    │  Backend    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Supabase  │    │   Session   │    │   Vector    │
│  Database   │    │   Storage   │    │   Storage   │
│             │    │             │    │ (ChromaDB)  │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Azure     │    │   Azure     │    │   Azure     │
│ PostgreSQL  │    │ Blob Storage│    │ AI Search   │
│             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SECURITY LAYER                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│   Nginx     │───▶│   Rate      │
│ Request     │    │   Proxy     │    │ Limiting    │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                           ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   CORS      │───▶│   Security  │───▶│   Input     │
│ Protection  │    │   Headers   │    │ Validation  │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                           ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   JWT       │───▶│   Azure     │───▶│   API Key   │
│   Auth      │    │   AD B2C    │    │ Management  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 📊 Monitoring & Health Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   MONITORING & HEALTH LAYER                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Health    │───▶│ Prometheus  │───▶│   Grafana   │
│   Checks    │    │  Metrics    │    │ Dashboard   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Service   │    │   System    │    │   Alerting  │
│   Status    │    │   Metrics   │    │   System    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Log       │    │   Backup    │    │   Recovery  │
│ Aggregation │    │   System    │    │   System    │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🚀 Production Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRODUCTION DEPLOYMENT                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Docker    │───▶│   Docker    │───▶│   Docker    │
│  Compose    │    │   Images    │    │  Containers │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Multi-    │    │   Health    │    │   Resource  │
│   Stage     │    │   Checks    │    │   Limits    │
│   Builds    │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   SSL/TLS   │    │   Backup    │    │   Scaling   │
│   Security  │    │   System    │    │   Policies  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🔄 Complete System Interaction Flow

```
1. USER INITIATES VOICE CALL
   ┌─────────────┐
   │   User      │
   │  Makes      │
   │   Call      │
   └─────────────┘
           │
           ▼
   ┌─────────────┐
   │ Sarvam AI   │
   │ Voice       │
   │ Provider    │
   └─────────────┘
           │
           ▼
   ┌─────────────┐
   │ Node.js     │
   │ Realtime    │
   │ Backend     │
   └─────────────┘
           │
           ▼
   ┌─────────────┐
   │ Python      │
   │ Orchestrator│
   │ Backend     │
   └─────────────┘
           │
           ▼
   ┌─────────────┐
   │ LangChain   │
   │ Processing  │
   └─────────────┘
           │
           ▼
   ┌─────────────┐
   │ AI/LLM      │
   │ Services    │
   └─────────────┘
           │
           ▼
   ┌─────────────┐
   │ Response    │
   │ Generation  │
   └─────────────┘
           │
           ▼
   ┌─────────────┐
   │ TTS         │
   │ Conversion  │
   └─────────────┘
           │
           ▼
   ┌─────────────┐
   │ User        │
   │ Receives    │
   │ Response    │
   └─────────────┘
```

## 🎯 Key Components Summary

### Frontend Layer
- **Client Applications**: React Native, Flutter, Web Apps
- **Communication**: HTTP/HTTPS, WebSocket connections
- **Authentication**: JWT tokens, Azure AD B2C

### API Gateway Layer
- **Nginx Reverse Proxy**: SSL termination, load balancing, rate limiting
- **Security**: CORS, security headers, input validation
- **Routing**: Request distribution to appropriate services

### Application Layer
- **Node.js Realtime Backend**: WebSocket handling, voice processing, session management
- **Python Orchestrator Backend**: LangChain processing, intent detection, AI integration
- **Voice Providers**: Sarvam AI, Twilio, Vonage, AWS Connect

### Data Layer
- **Primary Database**: Azure PostgreSQL (production), Supabase (development)
- **Cache**: Redis for session management and performance
- **Storage**: Azure Blob Storage for file storage
- **Vector Database**: ChromaDB for AI embeddings

### AI/LLM Layer
- **Azure OpenAI**: Primary LLM service
- **OpenAI API**: Fallback LLM service
- **LangChain**: AI orchestration and tool integration

### Monitoring Layer
- **Prometheus**: Metrics collection
- **Grafana**: Dashboard and visualization
- **Health Checks**: Service monitoring and alerting

### Security Layer
- **Authentication**: JWT, Azure AD B2C
- **Authorization**: Role-based access control
- **Protection**: Rate limiting, input validation, CORS
- **Encryption**: TLS/SSL for data in transit

This architecture provides a robust, scalable, and secure voice agent system that can handle multiple voice providers, AI processing, and real-time interactions while maintaining high availability and performance.













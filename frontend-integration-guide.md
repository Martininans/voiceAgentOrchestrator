# Frontend Integration Guide - Incremental Deployment

This guide shows how to integrate your frontend with the Voice Agent Orchestrator backend during incremental deployment.

## 🎯 **Integration Strategy**

Your backend is designed as **API-first**, meaning any frontend can consume it. Here's how to integrate:

### **📡 API Endpoints**

#### **Production (Default)**
```javascript
const PRODUCTION_CONFIG = {
  orchestrator: 'http://localhost:8000',
  realtime: 'http://localhost:3000',
  websocket: 'ws://localhost:3000/ws'
};
```

#### **Staging (Testing)**
```javascript
const STAGING_CONFIG = {
  orchestrator: 'http://localhost:8001',
  realtime: 'http://localhost:3001',
  websocket: 'ws://localhost:3001/ws'
};
```

## 🔧 **Frontend Integration Examples**

### **1. React/Next.js Integration**

```javascript
// config/environment.js
const getConfig = () => {
  const isStaging = process.env.NEXT_PUBLIC_ENVIRONMENT === 'staging';
  
  return {
    orchestratorUrl: isStaging 
      ? 'http://localhost:8001' 
      : 'http://localhost:8000',
    realtimeUrl: isStaging 
      ? 'http://localhost:3001' 
      : 'http://localhost:3000',
    websocketUrl: isStaging 
      ? 'ws://localhost:3001/ws' 
      : 'ws://localhost:3000/ws'
  };
};

export default getConfig;
```

```javascript
// services/voiceAgent.js
import getConfig from '../config/environment';

const config = getConfig();

export class VoiceAgentService {
  constructor() {
    this.orchestratorUrl = config.orchestratorUrl;
    this.realtimeUrl = config.realtimeUrl;
    this.websocketUrl = config.websocketUrl;
  }

  // Text processing
  async processText(text, userId, sessionId) {
    const response = await fetch(`${this.orchestratorUrl}/process-intent`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        user_id: userId,
        session_id: sessionId
      })
    });
    
    return response.json();
  }

  // Audio processing
  async processAudio(audioData, userId, sessionId) {
    const response = await fetch(`${this.orchestratorUrl}/process-audio`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        audio_data: audioData,
        user_id: userId,
        session_id: sessionId
      })
    });
    
    return response.json();
  }

  // WebSocket connection
  connectWebSocket(userId, sessionId) {
    const ws = new WebSocket(this.websocketUrl);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      ws.send(JSON.stringify({
        type: 'auth',
        user_id: userId,
        session_id: sessionId
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleWebSocketMessage(data);
    };

    return ws;
  }

  handleWebSocketMessage(data) {
    switch (data.type) {
      case 'audio_response':
        // Handle audio response
        break;
      case 'text_response':
        // Handle text response
        break;
      case 'error':
        console.error('WebSocket error:', data.message);
        break;
    }
  }
}
```

### **2. Vue.js Integration**

```javascript
// services/voiceAgent.js
import { ref, reactive } from 'vue';

const config = reactive({
  orchestratorUrl: import.meta.env.VITE_ENVIRONMENT === 'staging' 
    ? 'http://localhost:8001' 
    : 'http://localhost:8000',
  realtimeUrl: import.meta.env.VITE_ENVIRONMENT === 'staging' 
    ? 'http://localhost:3001' 
    : 'http://localhost:3000',
  websocketUrl: import.meta.env.VITE_ENVIRONMENT === 'staging' 
    ? 'ws://localhost:3001/ws' 
    : 'ws://localhost:3000/ws'
});

export function useVoiceAgent() {
  const isConnected = ref(false);
  const messages = ref([]);
  let ws = null;

  const connect = (userId, sessionId) => {
    ws = new WebSocket(config.websocketUrl);
    
    ws.onopen = () => {
      isConnected.value = true;
      ws.send(JSON.stringify({
        type: 'auth',
        user_id: userId,
        session_id: sessionId
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      messages.value.push(data);
    };
  };

  const sendText = async (text, userId, sessionId) => {
    const response = await fetch(`${config.orchestratorUrl}/process-intent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, user_id: userId, session_id: sessionId })
    });
    
    return response.json();
  };

  return {
    config,
    isConnected,
    messages,
    connect,
    sendText
  };
}
```

### **3. Angular Integration**

```typescript
// services/voice-agent.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class VoiceAgentService {
  private config = {
    orchestratorUrl: environment.staging 
      ? 'http://localhost:8001' 
      : 'http://localhost:8000',
    realtimeUrl: environment.staging 
      ? 'http://localhost:3001' 
      : 'http://localhost:3000',
    websocketUrl: environment.staging 
      ? 'ws://localhost:3001/ws' 
      : 'ws://localhost:3000/ws'
  };

  private ws: WebSocket | null = null;
  public messages$ = new Subject<any>();

  constructor(private http: HttpClient) {}

  processText(text: string, userId: string, sessionId: string): Observable<any> {
    return this.http.post(`${this.config.orchestratorUrl}/process-intent`, {
      text,
      user_id: userId,
      session_id: sessionId
    });
  }

  processAudio(audioData: string, userId: string, sessionId: string): Observable<any> {
    return this.http.post(`${this.config.orchestratorUrl}/process-audio`, {
      audio_data: audioData,
      user_id: userId,
      session_id: sessionId
    });
  }

  connectWebSocket(userId: string, sessionId: string): void {
    this.ws = new WebSocket(this.config.websocketUrl);
    
    this.ws.onopen = () => {
      this.ws?.send(JSON.stringify({
        type: 'auth',
        user_id: userId,
        session_id: sessionId
      }));
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.messages$.next(data);
    };
  }
}
```

## 🚀 **Deployment Workflow**

### **Step 1: Deploy Staging**
```bash
# Deploy backend to staging
./deploy-incremental.sh staging
```

### **Step 2: Test with Frontend**
```bash
# Set environment to staging
export NEXT_PUBLIC_ENVIRONMENT=staging  # React/Next.js
export VITE_ENVIRONMENT=staging         # Vue.js
# or update environment.ts for Angular
```

### **Step 3: Deploy Production**
```bash
# Deploy backend to production
./deploy-incremental.sh production
```

### **Step 4: Switch Frontend**
```bash
# Switch to production
export NEXT_PUBLIC_ENVIRONMENT=production
export VITE_ENVIRONMENT=production
```

## 🔍 **Testing Your Integration**

### **Health Checks**
```bash
# Test orchestrator
curl http://localhost:8000/health  # Production
curl http://localhost:8001/health  # Staging

# Test realtime
curl http://localhost:3000/health  # Production
curl http://localhost:3001/health  # Staging
```

### **WebSocket Test**
```javascript
// Test WebSocket connection
const ws = new WebSocket('ws://localhost:3000/ws'); // or 3001 for staging
ws.onopen = () => console.log('Connected!');
ws.onmessage = (event) => console.log('Message:', JSON.parse(event.data));
```

## 📋 **Environment Variables**

### **React/Next.js (.env.local)**
```env
NEXT_PUBLIC_ENVIRONMENT=staging  # or production
NEXT_PUBLIC_ORCHESTRATOR_URL=http://localhost:8001
NEXT_PUBLIC_REALTIME_URL=http://localhost:3001
```

### **Vue.js (.env)**
```env
VITE_ENVIRONMENT=staging  # or production
VITE_ORCHESTRATOR_URL=http://localhost:8001
VITE_REALTIME_URL=http://localhost:3001
```

### **Angular (environment.ts)**
```typescript
export const environment = {
  production: false,
  staging: true,
  orchestratorUrl: 'http://localhost:8001',
  realtimeUrl: 'http://localhost:3001'
};
```

## 🎯 **Key Benefits of This Approach**

1. **Zero Downtime**: Frontend continues working while backend deploys
2. **Safe Testing**: Test new backend features in staging
3. **Easy Rollback**: Can quickly switch back to previous version
4. **Independent Scaling**: Frontend and backend can scale separately
5. **Feature Flags**: Can gradually roll out new features

## 🚨 **Important Notes**

- **CORS**: Backend is configured to allow all origins (`CORS_ORIGIN=*`)
- **WebSocket**: Supports real-time communication for voice/audio
- **Authentication**: JWT-based authentication supported
- **Health Checks**: Use `/health` endpoints to monitor service status
- **Error Handling**: Always implement proper error handling in frontend

This setup allows you to deploy your backend services incrementally while your frontend continues to work seamlessly! 
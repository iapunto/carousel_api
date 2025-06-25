# 💻 Ejemplos de Código

Colección completa de ejemplos de código para integración con carousel_api v2.6.0 en diferentes lenguajes de programación y frameworks.

---

## 📋 Índice de Ejemplos

### Por Lenguaje

- **[Python](#-python)** - Requests, aiohttp, WebSocket
- **[JavaScript](#-javascript)** - Fetch API, Axios, WebSocket
- **[C#](#-c)** - HttpClient, WebSocket
- **[Java](#-java)** - HttpClient, WebSocket
- **[PHP](#-php)** - cURL, Guzzle
- **[Node.js](#-nodejs)** - Express integration

### Por Funcionalidad

- **[API REST](#-ejemplos-api-rest)** - CRUD operations
- **[WebSocket](#-ejemplos-websocket)** - Real-time communication
- **[Integración WMS](#-integración-wms)** - Complete WMS integration
- **[Monitoreo](#-monitoreo-y-alertas)** - Health checks y monitoring

---

## 🐍 Python

### Ejemplo Básico con Requests

```python
#!/usr/bin/env python3
"""
Ejemplo básico de integración con carousel_api usando requests
"""

import requests
import json
import time
from typing import Dict, List, Optional

class CarouselAPIClient:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CarouselAPI-Python-Client/1.0'
        })
    
    def get_machines(self) -> List[Dict]:
        """Obtener lista de máquinas disponibles"""
        response = self.session.get(f"{self.base_url}/v1/machines")
        response.raise_for_status()
        return response.json()['data']
    
    def get_machine_status(self, machine_id: str) -> Dict:
        """Obtener estado de una máquina específica"""
        response = self.session.get(f"{self.base_url}/v1/machines/{machine_id}/status")
        response.raise_for_status()
        return response.json()['data']
    
    def move_to_position(self, machine_id: str, position: int) -> Dict:
        """Mover carrusel a posición específica"""
        payload = {
            "command": 1,
            "argument": position
        }
        response = self.session.post(
            f"{self.base_url}/v1/machines/{machine_id}/command",
            json=payload
        )
        response.raise_for_status()
        return response.json()['data']
    
    def wait_for_movement_completion(self, machine_id: str, timeout: int = 30) -> bool:
        """Esperar hasta que el movimiento se complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_machine_status(machine_id)
            if status['status']['RUN'] == 'Detenido':
                return True
            time.sleep(1)
        
        return False

# Ejemplo de uso
def main():
    client = CarouselAPIClient()
    
    try:
        # Listar máquinas
        machines = client.get_machines()
        print(f"Máquinas disponibles: {len(machines)}")
        
        for machine in machines:
            machine_id = machine['id']
            print(f"\n--- {machine['name']} ---")
            
            # Obtener estado
            status = client.get_machine_status(machine_id)
            print(f"Estado: {status['status']}")
            print(f"Posición actual: {status['position']}")
            
            # Mover a posición 10
            if status['status']['RUN'] == 'Detenido':
                print("Moviendo a posición 10...")
                result = client.move_to_position(machine_id, 10)
                print(f"Comando enviado: {result}")
                
                # Esperar completado
                if client.wait_for_movement_completion(machine_id):
                    print("✅ Movimiento completado")
                else:
                    print("⚠️ Timeout esperando movimiento")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de API: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
```

### Ejemplo Asíncrono con aiohttp

```python
#!/usr/bin/env python3
"""
Cliente asíncrono para carousel_api usando aiohttp
"""

import aiohttp
import asyncio
import json
from typing import Dict, List

class AsyncCarouselClient:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
    
    async def get_machines(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Obtener lista de máquinas"""
        async with session.get(f"{self.base_url}/v1/machines") as response:
            response.raise_for_status()
            data = await response.json()
            return data['data']
    
    async def get_machine_status(self, session: aiohttp.ClientSession, machine_id: str) -> Dict:
        """Obtener estado de máquina"""
        async with session.get(f"{self.base_url}/v1/machines/{machine_id}/status") as response:
            response.raise_for_status()
            data = await response.json()
            return data['data']
    
    async def move_machine(self, session: aiohttp.ClientSession, machine_id: str, position: int) -> Dict:
        """Mover máquina a posición"""
        payload = {"command": 1, "argument": position}
        async with session.post(
            f"{self.base_url}/v1/machines/{machine_id}/command",
            json=payload
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data['data']
    
    async def monitor_multiple_machines(self, machine_ids: List[str]):
        """Monitorear múltiples máquinas concurrentemente"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for machine_id in machine_ids:
                task = self.get_machine_status(session, machine_id)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for machine_id, result in zip(machine_ids, results):
                if isinstance(result, Exception):
                    print(f"❌ {machine_id}: {result}")
                else:
                    print(f"✅ {machine_id}: {result['status']}")

# Ejemplo de uso
async def main():
    client = AsyncCarouselClient()
    
    async with aiohttp.ClientSession() as session:
        try:
            # Obtener máquinas
            machines = await client.get_machines(session)
            machine_ids = [m['id'] for m in machines]
            
            # Monitorear todas las máquinas
            await client.monitor_multiple_machines(machine_ids)
            
            # Mover máquinas concurrentemente
            tasks = []
            for i, machine_id in enumerate(machine_ids[:3]):  # Solo primeras 3
                position = 10 + i * 5  # Posiciones 10, 15, 20
                task = client.move_machine(session, machine_id, position)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            print("Movimientos iniciados:", results)
        
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🌐 JavaScript

### Ejemplo con Fetch API

```javascript
/**
 * Cliente JavaScript para carousel_api usando Fetch API
 */

class CarouselAPIClient {
    constructor(baseURL = 'http://localhost:5000') {
        this.baseURL = baseURL.replace(/\/$/, '');
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'User-Agent': 'CarouselAPI-JS-Client/1.0'
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.defaultHeaders,
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`HTTP ${response.status}: ${errorData.error || response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API Request failed: ${error.message}`);
            throw error;
        }
    }

    async getMachines() {
        const response = await this.request('/v1/machines');
        return response.data;
    }

    async getMachineStatus(machineId) {
        const response = await this.request(`/v1/machines/${machineId}/status`);
        return response.data;
    }

    async moveToPosition(machineId, position) {
        const response = await this.request(`/v1/machines/${machineId}/command`, {
            method: 'POST',
            body: JSON.stringify({
                command: 1,
                argument: position
            })
        });
        return response.data;
    }

    async waitForMovementCompletion(machineId, timeoutMs = 30000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeoutMs) {
            const status = await this.getMachineStatus(machineId);
            if (status.status.RUN === 'Detenido') {
                return true;
            }
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        return false;
    }
}

// Ejemplo de uso
async function main() {
    const client = new CarouselAPIClient();
    
    try {
        // Obtener máquinas
        const machines = await client.getMachines();
        console.log(`Máquinas disponibles: ${machines.length}`);
        
        for (const machine of machines) {
            console.log(`\n--- ${machine.name} ---`);
            
            // Obtener estado
            const status = await client.getMachineStatus(machine.id);
            console.log('Estado:', status.status);
            console.log('Posición:', status.position);
            
            // Mover si está detenido
            if (status.status.RUN === 'Detenido') {
                console.log('Moviendo a posición 15...');
                await client.moveToPosition(machine.id, 15);
                
                const completed = await client.waitForMovementCompletion(machine.id);
                console.log(completed ? '✅ Completado' : '⚠️ Timeout');
            }
        }
    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

// Ejecutar si está en Node.js
if (typeof require !== 'undefined' && require.main === module) {
    main();
}
```

### Ejemplo con WebSocket en JavaScript

```javascript
/**
 * Cliente WebSocket para carousel_api
 */

class CarouselWebSocketClient {
    constructor(wsURL = 'ws://localhost:8765') {
        this.wsURL = wsURL;
        this.ws = null;
        this.messageHandlers = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }

    connect() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.wsURL);
                
                this.ws.onopen = () => {
                    console.log('✅ WebSocket conectado');
                    this.reconnectAttempts = 0;
                    resolve();
                };
                
                this.ws.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    } catch (error) {
                        console.error('Error parsing message:', error);
                    }
                };
                
                this.ws.onclose = () => {
                    console.log('🔌 WebSocket desconectado');
                    this.attemptReconnect();
                };
                
                this.ws.onerror = (error) => {
                    console.error('❌ WebSocket error:', error);
                    reject(error);
                };
                
            } catch (error) {
                reject(error);
            }
        });
    }

    handleMessage(message) {
        const handler = this.messageHandlers.get(message.type);
        if (handler) {
            handler(message);
        } else {
            console.log('Mensaje recibido:', message);
        }
    }

    onMessage(type, handler) {
        this.messageHandlers.set(type, handler);
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('WebSocket no está conectado');
        }
    }

    subscribeToStatusUpdates() {
        this.send({
            type: 'subscribe',
            subscription_type: 'status_updates'
        });
    }

    requestMachineStatus(machineId) {
        this.send({
            type: 'get_status',
            machine_id: machineId
        });
    }

    sendCommand(machineId, command, argument) {
        this.send({
            type: 'send_command',
            machine_id: machineId,
            command: command,
            argument: argument
        });
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`Reintentando conexión en ${delay}ms... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect().catch(console.error);
            }, delay);
        } else {
            console.error('❌ Máximo número de reintentos alcanzado');
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Ejemplo de uso
async function websocketExample() {
    const client = new CarouselWebSocketClient();
    
    // Configurar manejadores de mensajes
    client.onMessage('welcome', (message) => {
        console.log('Bienvenida:', message.message);
        client.subscribeToStatusUpdates();
    });
    
    client.onMessage('status_update', (message) => {
        console.log(`Estado ${message.machine_id}:`, message.data.status);
    });
    
    client.onMessage('command_result', (message) => {
        console.log(`Comando ${message.machine_id}:`, message.result);
    });
    
    try {
        await client.connect();
        
        // Solicitar estado de máquina específica
        setTimeout(() => {
            client.requestMachineStatus('machine_1');
        }, 1000);
        
        // Enviar comando después de 3 segundos
        setTimeout(() => {
            client.sendCommand('machine_1', 1, 20);
        }, 3000);
        
    } catch (error) {
        console.error('Error conectando WebSocket:', error);
    }
}
```

---

## 🔷 C #

### Ejemplo con HttpClient

```csharp
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace CarouselAPI.Client
{
    public class CarouselAPIClient : IDisposable
    {
        private readonly HttpClient _httpClient;
        private readonly string _baseUrl;

        public CarouselAPIClient(string baseUrl = "http://localhost:5000")
        {
            _baseUrl = baseUrl.TrimEnd('/');
            _httpClient = new HttpClient();
            _httpClient.DefaultRequestHeaders.Add("User-Agent", "CarouselAPI-CSharp-Client/1.0");
        }

        public async Task<List<Machine>> GetMachinesAsync()
        {
            var response = await _httpClient.GetAsync($"{_baseUrl}/v1/machines");
            response.EnsureSuccessStatusCode();
            
            var json = await response.Content.ReadAsStringAsync();
            var apiResponse = JsonSerializer.Deserialize<ApiResponse<List<Machine>>>(json);
            
            return apiResponse.Data;
        }

        public async Task<MachineStatus> GetMachineStatusAsync(string machineId)
        {
            var response = await _httpClient.GetAsync($"{_baseUrl}/v1/machines/{machineId}/status");
            response.EnsureSuccessStatusCode();
            
            var json = await response.Content.ReadAsStringAsync();
            var apiResponse = JsonSerializer.Deserialize<ApiResponse<MachineStatus>>(json);
            
            return apiResponse.Data;
        }

        public async Task<CommandResult> MoveToPositionAsync(string machineId, int position)
        {
            var command = new
            {
                command = 1,
                argument = position
            };

            var json = JsonSerializer.Serialize(command);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync($"{_baseUrl}/v1/machines/{machineId}/command", content);
            response.EnsureSuccessStatusCode();
            
            var responseJson = await response.Content.ReadAsStringAsync();
            var apiResponse = JsonSerializer.Deserialize<ApiResponse<CommandResult>>(responseJson);
            
            return apiResponse.Data;
        }

        public async Task<bool> WaitForMovementCompletionAsync(string machineId, TimeSpan timeout)
        {
            var startTime = DateTime.Now;
            
            while (DateTime.Now - startTime < timeout)
            {
                var status = await GetMachineStatusAsync(machineId);
                if (status.Status.RUN == "Detenido")
                {
                    return true;
                }
                
                await Task.Delay(1000);
            }
            
            return false;
        }

        public void Dispose()
        {
            _httpClient?.Dispose();
        }
    }

    // Modelos de datos
    public class ApiResponse<T>
    {
        public bool Success { get; set; }
        public T Data { get; set; }
        public string Error { get; set; }
        public string Code { get; set; }
    }

    public class Machine
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public string Ip { get; set; }
        public int Port { get; set; }
        public string Type { get; set; }
        public string Status { get; set; }
        public string Description { get; set; }
    }

    public class MachineStatus
    {
        public StatusDetails Status { get; set; }
        public int Position { get; set; }
        public int RawStatus { get; set; }
        public string ConnectionStatus { get; set; }
        public DateTime LastUpdate { get; set; }
    }

    public class StatusDetails
    {
        public string READY { get; set; }
        public string RUN { get; set; }
        public string MODO_OPERACION { get; set; }
        public string ALARMA { get; set; }
    }

    public class CommandResult
    {
        public int CommandSent { get; set; }
        public int Argument { get; set; }
        public string Result { get; set; }
        public DateTime Timestamp { get; set; }
    }

    // Ejemplo de uso
    class Program
    {
        static async Task Main(string[] args)
        {
            using var client = new CarouselAPIClient();
            
            try
            {
                // Obtener máquinas
                var machines = await client.GetMachinesAsync();
                Console.WriteLine($"Máquinas disponibles: {machines.Count}");
                
                foreach (var machine in machines)
                {
                    Console.WriteLine($"\n--- {machine.Name} ---");
                    
                    // Obtener estado
                    var status = await client.GetMachineStatusAsync(machine.Id);
                    Console.WriteLine($"Estado: {status.Status.RUN}");
                    Console.WriteLine($"Posición: {status.Position}");
                    
                    // Mover si está detenido
                    if (status.Status.RUN == "Detenido")
                    {
                        Console.WriteLine("Moviendo a posición 30...");
                        var result = await client.MoveToPositionAsync(machine.Id, 30);
                        Console.WriteLine($"Comando enviado: {result.Result}");
                        
                        var completed = await client.WaitForMovementCompletionAsync(
                            machine.Id, 
                            TimeSpan.FromSeconds(30)
                        );
                        
                        Console.WriteLine(completed ? "✅ Completado" : "⚠️ Timeout");
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Error: {ex.Message}");
            }
        }
    }
}
```

---

## 🐘 PHP

### Ejemplo con cURL

```php
<?php
/**
 * Cliente PHP para carousel_api usando cURL
 */

class CarouselAPIClient {
    private $baseUrl;
    private $defaultHeaders;

    public function __construct($baseUrl = 'http://localhost:5000') {
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->defaultHeaders = [
            'Content-Type: application/json',
            'User-Agent: CarouselAPI-PHP-Client/1.0'
        ];
    }

    private function makeRequest($endpoint, $method = 'GET', $data = null) {
        $url = $this->baseUrl . $endpoint;
        
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => $this->defaultHeaders,
            CURLOPT_TIMEOUT => 30,
            CURLOPT_CONNECTTIMEOUT => 10,
            CURLOPT_CUSTOMREQUEST => $method
        ]);

        if ($data !== null) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);

        if ($error) {
            throw new Exception("cURL Error: " . $error);
        }

        $decodedResponse = json_decode($response, true);
        
        if ($httpCode >= 400) {
            $errorMessage = $decodedResponse['error'] ?? "HTTP $httpCode";
            throw new Exception($errorMessage);
        }

        return $decodedResponse;
    }

    public function getMachines() {
        $response = $this->makeRequest('/v1/machines');
        return $response['data'];
    }

    public function getMachineStatus($machineId) {
        $response = $this->makeRequest("/v1/machines/$machineId/status");
        return $response['data'];
    }

    public function moveToPosition($machineId, $position) {
        $data = [
            'command' => 1,
            'argument' => $position
        ];
        
        $response = $this->makeRequest("/v1/machines/$machineId/command", 'POST', $data);
        return $response['data'];
    }

    public function waitForMovementCompletion($machineId, $timeoutSeconds = 30) {
        $startTime = time();
        
        while (time() - $startTime < $timeoutSeconds) {
            $status = $this->getMachineStatus($machineId);
            
            if ($status['status']['RUN'] === 'Detenido') {
                return true;
            }
            
            sleep(1);
        }
        
        return false;
    }
}

// Ejemplo de uso
try {
    $client = new CarouselAPIClient();
    
    // Obtener máquinas
    $machines = $client->getMachines();
    echo "Máquinas disponibles: " . count($machines) . "\n";
    
    foreach ($machines as $machine) {
        echo "\n--- {$machine['name']} ---\n";
        
        // Obtener estado
        $status = $client->getMachineStatus($machine['id']);
        echo "Estado: " . json_encode($status['status']) . "\n";
        echo "Posición: {$status['position']}\n";
        
        // Mover si está detenido
        if ($status['status']['RUN'] === 'Detenido') {
            echo "Moviendo a posición 35...\n";
            $result = $client->moveToPosition($machine['id'], 35);
            echo "Comando enviado: {$result['result']}\n";
            
            $completed = $client->waitForMovementCompletion($machine['id']);
            echo $completed ? "✅ Completado\n" : "⚠️ Timeout\n";
        }
    }
    
} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
}
?>
```

---

## 🟢 Node.js

### Integración con Express

```javascript
/**
 * Middleware Express para integración con carousel_api
 */

const express = require('express');
const axios = require('axios');
const WebSocket = require('ws');

class CarouselMiddleware {
    constructor(apiBaseUrl = 'http://localhost:5000', wsUrl = 'ws://localhost:8765') {
        this.apiBaseUrl = apiBaseUrl.replace(/\/$/, '');
        this.wsUrl = wsUrl;
        this.wsClient = null;
        this.statusCache = new Map();
        this.cacheTimeout = 5000; // 5 segundos
    }

    // Middleware para verificar conectividad
    async healthCheck(req, res, next) {
        try {
            const response = await axios.get(`${this.apiBaseUrl}/v1/machines`, {
                timeout: 5000
            });
            
            req.carouselAPI = {
                available: true,
                machines: response.data.data
            };
            
            next();
        } catch (error) {
            req.carouselAPI = {
                available: false,
                error: error.message
            };
            next();
        }
    }

    // Middleware para cache de estados
    async statusCache(req, res, next) {
        const machineId = req.params.machineId;
        const cacheKey = `status_${machineId}`;
        const cached = this.statusCache.get(cacheKey);
        
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            req.cachedStatus = cached.data;
            next();
            return;
        }

        try {
            const response = await axios.get(`${this.apiBaseUrl}/v1/machines/${machineId}/status`);
            const statusData = {
                data: response.data.data,
                timestamp: Date.now()
            };
            
            this.statusCache.set(cacheKey, statusData);
            req.cachedStatus = statusData.data;
            next();
        } catch (error) {
            res.status(500).json({ error: 'Error fetching machine status' });
        }
    }

    // Conectar WebSocket para actualizaciones en tiempo real
    connectWebSocket() {
        this.wsClient = new WebSocket(this.wsUrl);
        
        this.wsClient.on('open', () => {
            console.log('✅ WebSocket conectado');
            this.wsClient.send(JSON.stringify({
                type: 'subscribe',
                subscription_type: 'status_updates'
            }));
        });
        
        this.wsClient.on('message', (data) => {
            try {
                const message = JSON.parse(data);
                if (message.type === 'status_update') {
                    // Actualizar cache
                    const cacheKey = `status_${message.machine_id}`;
                    this.statusCache.set(cacheKey, {
                        data: message.data,
                        timestamp: Date.now()
                    });
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        });
        
        this.wsClient.on('close', () => {
            console.log('🔌 WebSocket desconectado, reintentando...');
            setTimeout(() => this.connectWebSocket(), 5000);
        });
    }
}

// Configurar Express app
const app = express();
const carousel = new CarouselMiddleware();

app.use(express.json());

// Conectar WebSocket
carousel.connectWebSocket();

// Rutas con middleware
app.get('/api/health', carousel.healthCheck.bind(carousel), (req, res) => {
    res.json({
        carousel_api: req.carouselAPI.available,
        machines_count: req.carouselAPI.machines?.length || 0,
        error: req.carouselAPI.error || null
    });
});

app.get('/api/machines', carousel.healthCheck.bind(carousel), (req, res) => {
    if (!req.carouselAPI.available) {
        return res.status(503).json({ error: 'Carousel API not available' });
    }
    
    res.json({
        success: true,
        data: req.carouselAPI.machines
    });
});

app.get('/api/machines/:machineId/status', 
    carousel.statusCache.bind(carousel), 
    (req, res) => {
        res.json({
            success: true,
            data: req.cachedStatus,
            cached: true
        });
    }
);

app.post('/api/machines/:machineId/move', async (req, res) => {
    const { machineId } = req.params;
    const { position } = req.body;
    
    if (!position || position < 1 || position > 255) {
        return res.status(400).json({ error: 'Invalid position' });
    }
    
    try {
        const response = await axios.post(
            `${carousel.apiBaseUrl}/v1/machines/${machineId}/command`,
            {
                command: 1,
                argument: position
            }
        );
        
        res.json({
            success: true,
            data: response.data.data
        });
    } catch (error) {
        res.status(error.response?.status || 500).json({
            error: error.response?.data?.error || error.message
        });
    }
});

// Endpoint para múltiples operaciones
app.post('/api/batch-operations', async (req, res) => {
    const { operations } = req.body;
    
    try {
        const promises = operations.map(async (op) => {
            try {
                const response = await axios.post(
                    `${carousel.apiBaseUrl}/v1/machines/${op.machineId}/command`,
                    {
                        command: op.command,
                        argument: op.argument
                    }
                );
                
                return {
                    machineId: op.machineId,
                    success: true,
                    data: response.data.data
                };
            } catch (error) {
                return {
                    machineId: op.machineId,
                    success: false,
                    error: error.response?.data?.error || error.message
                };
            }
        });
        
        const results = await Promise.all(promises);
        
        res.json({
            success: true,
            results: results
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Iniciar servidor
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 Servidor Express ejecutándose en puerto ${PORT}`);
    console.log(`🔗 Conectado a Carousel API: ${carousel.apiBaseUrl}`);
});

module.exports = { app, CarouselMiddleware };
```

---

## 🔗 Enlaces Relacionados

- **[API REST Reference](API-REST-Reference)** - Documentación completa de endpoints
- **[WebSocket API](WebSocket-API)** - Comunicación en tiempo real
- **[Guía de Integración WMS](Guía-de-Integración-WMS)** - Integración completa con WMS
- **[Códigos de Estado y Errores](Códigos-de-Estado-y-Errores)** - Manejo de errores

---

## 📞 Soporte

Para ejemplos adicionales o soporte con integración:

- 🐛 **Issues:** [GitHub Issues](https://github.com/iapunto/carousel_api/issues)
- 📧 **Email:** <soporte@iapunto.com>
- 📚 **Documentación:** [Wiki Principal](Home)
- 💻 **Ejemplos en GitHub:** [Repository Examples](https://github.com/iapunto/carousel_api/tree/main/examples)

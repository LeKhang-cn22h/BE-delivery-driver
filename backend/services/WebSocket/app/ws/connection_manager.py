from typing import Dict
from uuid import UUID
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # driver_id cho việc broadcast đến đúng viewer
        self.viewers:Dict[str, list[WebSocket]] = {}
        # admin xem tất cả driver
        self.admin_viewers: list[WebSocket] = []
        self.driver_viewers: list[WebSocket] = []
        self.customer_viewers: list[WebSocket] = []

        self.active_connections: list[WebSocket] = []

    async def connect_viewer(self, driver_id: UUID, ws: WebSocket):
        await ws.accept()
        if driver_id not in self.viewers:
            self.viewers[driver_id] = []
        self.viewers[driver_id].append(ws)
        print(f"Viewer connected for driver {driver_id}. Total viewers: {len(self.viewers[driver_id])}")

    

    async def connect_admin(self, ws: WebSocket):
        await ws.accept()
        self.admin_viewers.append(ws)
        print(f"Admin viewer connected. Total admin viewers: {len(self.admin_viewers)}")

    async def connect_driver(self, ws: WebSocket):
        await ws.accept()
        self.driver_viewers.append(ws)
        print(f"Driver viewer connected. Total driver viewers: {len(self.driver_viewers)}")
    
    async def connect_customer(self, ws: WebSocket):
        await ws.accept()
        self.customer_viewers.append(ws)
        print(f"Customer viewer connected. Total customer viewers: {len(self.customer_viewers)}")
    
    def disconnect_viewer(self, ws: WebSocket, driver_id: UUID):
        if driver_id in self.viewers and ws in self.viewers[driver_id]:
            self.viewers[driver_id].remove(ws)
            print(f"Viewer disconnected for driver {driver_id}. Total viewers: {len(self.viewers[driver_id])}")

    def disconnect_admin(self, ws: WebSocket):
        if ws in self.admin_viewers:
            self.admin_viewers.remove(ws)
            print(f"Admin viewer disconnected. Total admin viewers: {len(self.admin_viewers)}")
    
    def disconnect_driver(self, ws: WebSocket):
        if ws in self.driver_viewers:
            self.driver_viewers.remove(ws)
            print(f"Driver viewer disconnected. Total driver viewers: {len(self.driver_viewers)}")

    def disconnect_customer(self, ws: WebSocket):
        if ws in self.customer_viewers:
            self.customer_viewers.remove(ws)
            print(f"Customer viewer disconnected. Total customer viewers: {len(self.customer_viewers)}")

    async def broadcast_to_viewers(self, driver_id: str, data: dict):
        """Gửi vị trí đến viewers đang theo dõi driver này"""
        if driver_id in self.viewers:
            dead = []
            for ws in self.viewers[driver_id]:
                try:
                    await ws.send_json(data)
                except:
                    dead.append(ws)
            for ws in dead:
                self.viewers[driver_id].remove(ws)
    
    async def broadcast_to_admins(self, data: dict):
        """Gửi vị trí đến tất cả admin"""
        dead = []
        for ws in self.admin_viewers:
            try:
                await ws.send_json(data)
            except:
                dead.append(ws)
        for ws in dead:
            self.admin_viewers.remove(ws)

    async def broadcast_to_drivers(self, data: dict):
        """Gửi vị trí đến tất cả driver viewers"""
        dead = []
        for ws in self.driver_viewers:
            try:
                await ws.send_json(data)
            except:
                dead.append(ws)
        for ws in dead:
            self.driver_viewers.remove(ws)
            
    async def broadcast_to_customers(self, data: dict):
        """Gửi vị trí đến tất cả customer viewers"""
        dead = []
        for ws in self.customer_viewers:
            try:
                await ws.send_json(data)
            except:
                dead.append(ws)
        for ws in dead:
            self.customer_viewers.remove(ws)


manager = ConnectionManager()
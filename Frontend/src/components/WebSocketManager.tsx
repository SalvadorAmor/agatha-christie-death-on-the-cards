
class WebSocketManager {
  private socket: WebSocket | null = null;

  constructor(token: string | null) {
    this.socket = token ? new WebSocket(`ws://localhost:8000/ws/monolithic?token=${token}`) : new WebSocket(`ws://localhost:8000/ws/monolithic`);
    this.socket.onopen = () => {
      console.log("WebSocket connected");
    }
    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("WebSocket message received:", data);
    }
  }


  public registerOnCreate(cb: (data: any) => void, model: string) {
    this.socket?.addEventListener('message', (event) => {
      console.log(event)
      const data = JSON.parse(event.data);
      if (data.action === 'create' && data.model === model) {
        cb(data.data);
      }
    });
  }

  public registerOnUpdate(cb: (data: any) => void, model: string) {
    this.socket?.addEventListener('message', (event) => {
      const data = JSON.parse(event.data);
      if (data.action === 'update' && data.model === model) {
        cb(data.data);
      }
    });
  }

  public registerOnDelete(cb: (data: any) => void, model: string) {
    this.socket?.addEventListener('message', (event) => {
      const data = JSON.parse(event.data);
      if (data.action === 'delete' && data.model === model) {
        cb(data.data);
      }
    });
  }

  public registerOnAction(cb: (data: any) => void, model: string, action: string) {
    this.socket?.addEventListener("message", (event) => {
      const data = JSON.parse(event.data);
      if (data.model === model && data.action === action) {
        cb(data.data);
      }
    });
  }

  public close() {
    this.socket?.close();
  }
}

export default WebSocketManager;

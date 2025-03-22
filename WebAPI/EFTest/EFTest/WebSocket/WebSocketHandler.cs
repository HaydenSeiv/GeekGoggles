using System;
using System.Collections.Generic;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;

namespace EFTest.WebSockets
{
    public class WebSocketHandler
    {
        private static List<WebSocket> _sockets = new List<WebSocket>();


        public async Task HandleWebSocketAsync(HttpContext context, WebSocket webSocket)
        {
            _sockets.Add(webSocket);
            byte[] buffer = new byte[1024 * 4];

            while (webSocket.State == WebSocketState.Open)
            {
                var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);
                if (result.MessageType == WebSocketMessageType.Text)
                {
                    string messageText = Encoding.UTF8.GetString(buffer, 0, result.Count);
                    Console.WriteLine($"Received: {messageText}");

                    // Send a response back
                    string response = $"Server received: {messageText}";
                    byte[] responseBytes = Encoding.UTF8.GetBytes(response);
                    await webSocket.SendAsync(new ArraySegment<byte>(responseBytes), WebSocketMessageType.Text, true, CancellationToken.None);
                }
                else if (result.MessageType == WebSocketMessageType.Close)
                {
                    Console.WriteLine("Client disconnected");
                    await webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", CancellationToken.None);
                    _sockets.Remove(webSocket);
                }
            }

        }
    }
}

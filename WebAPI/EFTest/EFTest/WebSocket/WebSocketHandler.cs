using System;
using System.Collections.Generic;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using EFTest.Models;
using Microsoft.AspNetCore.Http;
using Newtonsoft.Json;

namespace EFTest.WebSockets
{
    public class WebSocketHandler
    {
        private static List<WebSocket> _sockets = new List<WebSocket>();


        public async Task HandleWebSocketAsync(HttpContext context ,WebSocket webSocket)
        {
            _sockets.Add(webSocket);
            byte[] buffer = new byte[1024 * 4];
            WebSocketReceiveResult result = null;

            while (webSocket.State == WebSocketState.Open)
            {
                try
                {
                    result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);

                }catch(WebSocketException ex)
                {
                    Console.WriteLine($"Disco: {ex}");

                }

               // var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);
                if (result.MessageType == WebSocketMessageType.Text)
                {
                    string messageText = Encoding.UTF8.GetString(buffer, 0, result.Count);
                    Console.WriteLine($"Received: {messageText}");

                    // Send a response back
                    //string response = $"Server received: {messageText}";
                    var response = JsonConvert.SerializeObject(new SocketMsg
                    {
                        Command = "send_cat",
                        Message = "Please send a cat"
                        });
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

        public string ProcessMessage(string message)
        {
            return null;
        }


    }
}

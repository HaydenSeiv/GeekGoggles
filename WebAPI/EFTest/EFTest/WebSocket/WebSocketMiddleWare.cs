using EFTest.WebSockets;
using Microsoft.AspNetCore.WebSockets;
using System.Net.WebSockets;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using static System.Net.Mime.MediaTypeNames;

namespace EFTest.Middleware
{
    public class WebSocketMiddleWare
    {
        private readonly RequestDelegate _next;
        private readonly WebSocketHandler _handler;
        private readonly ILogger<WebSocketMiddleWare> _logger;

        public WebSocketMiddleWare(RequestDelegate next, WebSocketHandler handler, ILogger<WebSocketMiddleWare> logger)
        {
            _next = next;
            _handler = handler;
            _logger = logger;
        }
        

        public async Task InvokeAsync(HttpContext context)
        {
            if (context.Request.Path == "/ws")
            {
                if (context.WebSockets.IsWebSocketRequest)
                {
                    using var webSocket = await context.WebSockets.AcceptWebSocketAsync();
                    _logger.LogInformation("WebSocket connection established");
                    await _handler.HandleWebSocketAsync(context, webSocket);
                }
                else
                {
                    context.Response.StatusCode = 400;
                }
            }
            else
            {
                await _next(context);
            }
        }
    }
}

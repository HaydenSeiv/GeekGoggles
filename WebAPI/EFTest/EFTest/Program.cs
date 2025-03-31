using EFTest.Data;
using Microsoft.EntityFrameworkCore;
using Microsoft.OpenApi.Models;
using Swashbuckle.AspNetCore.SwaggerUI;
using Microsoft.AspNetCore.Identity;
using EFTest.Models;
using Microsoft.AspNetCore.JsonPatch;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.WebSockets;
using EFTest.WebSockets;
using MQTTnet;
using MQTTnet.Protocol;
using MQTTnet.Server;
var builder = WebApplication.CreateBuilder(args);

// Add this before building the app to listen on all interfaces
builder.WebHost.ConfigureKestrel(serverOptions =>
{
    serverOptions.ListenAnyIP(5099); // HTTP
    serverOptions.ListenAnyIP(7007, listenOptions =>  // HTTPS
    {
        listenOptions.UseHttps();
    });
});

// Add CORS policy
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAllOrigins",
        policy =>
        {
            policy.AllowAnyOrigin()
                  .AllowAnyMethod()
                  .AllowAnyHeader();
        });
});

builder.Services.AddControllers();
builder.Services.AddControllers().AddNewtonsoftJson();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();


var connectionString = builder.Configuration.GetConnectionString("AppDbConnectionString");
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseMySql(connectionString, ServerVersion.AutoDetect(connectionString)));
builder.Services.AddScoped<IPasswordHasher<User>, PasswordHasher<User>>();
builder.Services.AddScoped<FileHandlerService>();
builder.Services.AddScoped<WebSocketHandler>(); 


// Add WebSocket services
builder.Services.AddWebSockets(options => {
    options.KeepAliveInterval = TimeSpan.FromMinutes(2);
});


// Create MQTT broker service
builder.Services.AddSingleton<IMqttServer>(serviceProvider =>
{
    var mqttFactory = new MqttFactory();
    var mqttServer = mqttFactory.CreateMqttServer();
    return mqttServer;
});

var app = builder.Build();

// Apply CORS before other middleware
app.UseCors("AllowAllOrigins");

app.UseDeveloperExceptionPage();

// Enable Swagger for development
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();


//WebSocket Handling
app.UseWebSockets();
app.Use(async (context, next) =>
{
    if (context.WebSockets.IsWebSocketRequest)
    {
        using (var webSocket = await context.WebSockets.AcceptWebSocketAsync())
        {
            // Get WebSocketHandler instance from DI
            var webSocketHandler = context.RequestServices.GetRequiredService<WebSocketHandler>();

            // Now you can use the injected AppDbContext within your WebSocketHandler
            await webSocketHandler.HandleWebSocketAsync(context, webSocket);
        }
    }
    else
    {
        await next();
    }
});

//MQTT Broker Handling
var mqttServer = app.Services.GetRequiredService<IMqttServer>();
var mqttServerOptions = new MqttServerOptionsBuilder()
    .WithDefaultEndpoint()
    .WithDefaultEndpointPort(1883)
    .Build();
await mqttServer.StartAsync(mqttServerOptions);
Console.WriteLine("MQTT Broker is Running on Port 1883");
app.Run();
//app.UseDeveloperExceptionPage();

#region WebSocket !!Ignore!!

async Task HandleWebSocketConnection(System.Net.WebSockets.WebSocket webSocket)
{
    // Sample WebSocket handling code, you can modify this as per your needs
    var buffer = new byte[1024 * 4];
    while (webSocket.State == System.Net.WebSockets.WebSocketState.Open)
    {
        var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);

        if (result.MessageType == System.Net.WebSockets.WebSocketMessageType.Text)
        {
            var message = System.Text.Encoding.UTF8.GetString(buffer, 0, result.Count);
            Console.WriteLine($"Received message: {message}");

            // Here you can send a response back to the client
            var responseMessage = "Message received!";
            var responseBytes = System.Text.Encoding.UTF8.GetBytes(responseMessage);
            await webSocket.SendAsync(new ArraySegment<byte>(responseBytes), result.MessageType, result.EndOfMessage, CancellationToken.None);
        }
        else if (result.MessageType == System.Net.WebSockets.WebSocketMessageType.Close)
        {
            await webSocket.CloseAsync(System.Net.WebSockets.WebSocketCloseStatus.NormalClosure, "Closing connection", CancellationToken.None);
        }
    }
}
#endregion 

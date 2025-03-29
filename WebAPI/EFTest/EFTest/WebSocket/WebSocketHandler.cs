using System;
using System.Collections.Generic;
using System.Net.Sockets;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using DocumentFormat.OpenXml.Office2010.Excel;
using EFTest.Data;
using EFTest.Models;
using Microsoft.AspNetCore.Http;
using Newtonsoft.Json;

namespace EFTest.WebSockets
{
    public class WebSocketHandler
    {
        private readonly AppDbContext _appDbContext;
        private static List<WebSocket> _sockets = new List<WebSocket>();
        private readonly Dictionary<string, StringBuilder> _imageBuilders = new();
        private readonly Dictionary<string, int> _expectedChunks = new();
        private readonly List<DBFileWebModel> _dBImages = new();

        public WebSocketHandler(AppDbContext appDbContext)
        {
            _appDbContext = appDbContext;
        }
        public async Task HandleWebSocketAsync(HttpContext context, WebSocket webSocket)
        {
            _sockets.Add(webSocket);
            byte[] buffer = new byte[1024 * 4];
            WebSocketReceiveResult result = null;

            while (webSocket.State == WebSocketState.Open)
            {
                try
                {
                    result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);

                }
                catch (WebSocketException ex)
                {
                    Console.WriteLine($"Disco: {ex}");
                    Console.WriteLine("Client disconnected");
                    //await webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", CancellationToken.None);
                    //_sockets.Remove(webSocket);
                    string filePath = "test.bin"; // File to write to

                    // Sample byte array (could be any binary data)
                    byte[] data = { 0x41, 0x42, 0x43, 0x44, 0x45 }; // Represents "ABCDE" in ASCII

                    // Write the byte array to file
                    File.WriteAllBytes(filePath, data);
                    Console.WriteLine($"Data written to {filePath}");

                }

                // var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);
                if (result.MessageType == WebSocketMessageType.Text)
                {
                    string messageText = Encoding.UTF8.GetString(buffer, 0, result.Count);
                    Console.WriteLine($"Received: {messageText}");

                    var rData = JsonConvert.DeserializeObject<SocketMsg>(messageText);
                    //if (rData.fileData == null)
                    //{
                    switch (rData.command)
                    {
                        case "connected":
                            if( await SendAllFilesFromDB(webSocket))
                            {
                                Console.WriteLine("OnLoad Send DONE");
                            }
                            break;
                        case "here_is_the_cat_start":
                            Console.WriteLine("START");
                            _imageBuilders[rData.fileName] = new StringBuilder();
                            _expectedChunks[rData.fileName] = rData.totalChunks;
                            break;
                        case "here_is the_cat_chunk":
                            if (_imageBuilders.TryGetValue(rData.fileName, out var builder))
                            {
                                builder.Append(rData.fileData);
                            }
                            break;
                        case "here_is_the_cat_end":
                            Console.WriteLine("END");
                            if (_imageBuilders.TryGetValue(rData.fileName, out var completedBuilder))
                            {
                                string base64Data = completedBuilder.ToString();
                                byte[] imageBytes = Convert.FromBase64String(base64Data);

                                //save image
                                string savePath = Path.Combine("Client", rData.fileName);
                                //string savePath2 = Path.Combine("Client/upload", "CAT");

                                Console.WriteLine(savePath);
                                if (!Directory.Exists(savePath))
                                {
                                    Directory.CreateDirectory(savePath);
                                }
                                //File.WriteAllBytes(savePath, imageBytes);
                                //clean up
                                _imageBuilders.Remove(rData.fileName);
                                _expectedChunks.Remove(rData.fileName);
                                Console.WriteLine("SUCCESS! One ");
                            }
                            break;

                            //}


                    }

                }
                else if (result.MessageType == WebSocketMessageType.Close)
                {
                    Console.WriteLine("Client disconnected");
                    await webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", CancellationToken.None);
                    _sockets.Remove(webSocket);
                    string filePath = "test.bin"; // File to write to

                    // Sample byte array (could be any binary data)
                    byte[] data = { 0x41, 0x42, 0x43, 0x44, 0x45 }; // Represents "ABCDE" in ASCII

                    // Write the byte array to file
                    File.WriteAllBytes(filePath, data);
                    Console.WriteLine($"Data written to {filePath}");
                }
            }

        }
        async Task<bool> SendMessage(string sData, WebSocket webSocket)
        {
            try
            {
                byte[] responseBytes = Encoding.UTF8.GetBytes(sData);
                await webSocket.SendAsync(new ArraySegment<byte>(responseBytes), WebSocketMessageType.Text, true, CancellationToken.None);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to send data: {sData} \r\n {ex}");
                return false;
            }
            return true;
        }
        public List<DBFileWebModel> GetAllFilesfromDB()
        {
            var files = _appDbContext.MyFiles
                .Select(f => new DBFileWebModel
                {
                    ID = f.Id,
                    Name = f.Title.Contains(".") ? f.Title.Substring(0, f.Title.IndexOf('.')) : f.Title,
                    Data = f.FileData,
                    Type = f.FileType
                }).ToList();

            return files;

        }

        async Task<bool> SendAllFilesFromDB(WebSocket socket)
        {
            var allFiles = GetAllFilesfromDB();

            foreach (var file in allFiles)
            {
                try
                {
                    var image = JsonConvert.SerializeObject(new SocketMsg
                    {
                        command = $"on_load_file_transfer",
                        fileData = file.Data,
                        fileName = file.Name,
                        fileType = file.Type,
                        message = $"{file.Name} was sent from Server"
                    });
                    if (await SendMessage(image, socket))
                    {
                        Console.WriteLine("Onload send was successfull");
                    }
                    else
                    {
                        Console.WriteLine("Onload Send Error");
                    }
                }
                catch (SocketException ex)
                {
                    Console.WriteLine($"Socket Error while sending Images[DB] to the PI : {ex}");
                    return false;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error while sending Images[DB] to the PI : {ex}");
                    return false;
                }

            }

            return true;
        }

    }
}

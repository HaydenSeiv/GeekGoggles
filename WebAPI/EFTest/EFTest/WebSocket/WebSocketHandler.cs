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
using static System.Net.Mime.MediaTypeNames;
using Pv;
using System.Diagnostics;
using Microsoft.EntityFrameworkCore;

namespace EFTest.WebSockets
{
    public class WebSocketHandler
    {
        private readonly AppDbContext _appDbContext;
        public static List<WebSocket> _sockets = new List<WebSocket>();
        private readonly Dictionary<string, StringBuilder> _fileBuffers = new();
        private readonly List<PiFile> _completedFiles = new();
        string projName = null;
        public int projID = 1;
        SocketMsgWeb proj = null;



        const string accessKey = "M8I9Z/xtWRJC4Woocn3rOJtl+vmoD1Yx6a/ZEZcNbsd/r1SRK3/aTw==";
        Leopard leopard = Leopard.Create(accessKey);

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
                    SaveAllPiFiles();
                    Console.WriteLine("Pi Files have been Saved");
                    projName = null;
                }

                if (result.MessageType == WebSocketMessageType.Text)
                {
                    string messageText = Encoding.UTF8.GetString(buffer, 0, result.Count);
                    Console.WriteLine($"Received: {messageText}");

                    var rData = JsonConvert.DeserializeObject<SocketMsg>(messageText);
                    switch (rData.command)
                    {
                        case "connected":
                            //projName = rData.projName;
                            if (proj != null)
                            {
                                if (await SendAllFilesFromDB(webSocket))
                                {
                                    Console.WriteLine("Onload send success!");
                                }

                            }
                            break;
                        case var cmd when cmd.EndsWith("_start"):
                            Console.WriteLine($"Start {rData.fileName}");
                            _fileBuffers[rData.fileName] = new StringBuilder();
                            break;
                        case var cmd when cmd.EndsWith("_chunk"):
                            Console.WriteLine($"Chunk {rData.fileName}");
                            if (_fileBuffers.ContainsKey(rData.fileName))
                            {
                                _fileBuffers[rData.fileName].Append(rData.fileData);
                            }
                            break;
                        case var cmd when cmd.EndsWith("_end"):
                            Console.WriteLine($"End {rData.fileName}");
                            if (_fileBuffers.ContainsKey(rData.fileName))
                            {
                                _completedFiles.Add(new PiFile
                                {
                                    Name = rData.fileName,
                                    b64Data = _fileBuffers[rData.fileName].ToString(),
                                    Type = rData.fileType
                                });
                                _fileBuffers.Remove(rData.fileName);
                            }
                            break;
                    }

                }
                else if (result.MessageType == WebSocketMessageType.Close)
                {
                    Console.WriteLine("Client disconnected");
                    projName = null;
                    await webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", CancellationToken.None);
                    _sockets.Remove(webSocket);
                    SaveAllPiFiles();
                    Console.WriteLine("Pi Files have been Saved");
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
        public List<DBFileWebModel> GetAllFilesfromDB(int projID)
        {
            var files = _appDbContext.MyFiles.Where(f => f.ProjectID == projID)
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
            var allFiles = GetAllFilesfromDB(proj.proj_id);

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

        async public void SaveAllPiFiles()
        {
            string fRoot = $"Client/uploads/pi_pics/{projName}";
            if (!Directory.Exists(fRoot))
            {
                Directory.CreateDirectory(fRoot);
            }

            foreach (var file in _completedFiles)
            {
                var fPath = Path.Combine(fRoot, file.Name);
                byte[] fBin = Convert.FromBase64String(file.b64Data);
                if (file.Type == "audio/wav")
                {
                    short[] pcmData = ConvertBytesToShorts(fBin);
                    LeopardTranscript audRes = leopard.Process(pcmData);

                    //save transcript to file
                    var transciptPath = Path.Combine(fRoot, Path.GetFileNameWithoutExtension(file.Name) + ".txt");
                    await File.WriteAllTextAsync(transciptPath, audRes.TranscriptString);
                }
                else
                {
                    await File.WriteAllBytesAsync(fPath, fBin);
                }

                Console.WriteLine($"{file.Name} saved Successfully");
            }
            Console.WriteLine("All files have been saved");
            _completedFiles.Clear();
        }

        async public Task BroadCastMessageAsync(string message)
        {
            if (await SendMessage(message, _sockets.First()))
            {

                //Console.WriteLine(message);
                //retrieve message 
                proj = JsonConvert.DeserializeObject<SocketMsgWeb>(message);
                Console.WriteLine("Project Info send was successfull");

                if (proj != null)
                {
                    Console.WriteLine("ProjInfo Parsing Complete");
                }
                else
                {
                    Console.WriteLine("Error Parsing ProjInfo");
                }

            }
            else
            {
                Console.WriteLine("Error while sending Project Info - Socket");
            }
        }
        async public Task SendNewImage(int imageID)
        {
            var image = await _appDbContext.MyFiles.FirstOrDefaultAsync(i => i.Id == imageID);
            if (image == null)
            {
                return;
            }

            try
            {
                var iMsg = JsonConvert.SerializeObject(new SocketMsg
                {
                    command = $"new_image_upload",
                    fileData = image.FileData,
                    fileName = image.Title.Contains(".") ? image.Title.Substring(0, image.Title.IndexOf('.')) : image.Title,
                    fileType = image.FileType,
                    message = $"A new image was uploaded"

                });
                if (await SendMessage(iMsg, _sockets.First()))
                {
                    Console.WriteLine("New Image was send successfully");
                }
                else
                {
                    Console.WriteLine("New Image Send Error ");
                }
            }catch(Exception ex)
            {
                Console.WriteLine("New Image Send Error- Socket");
            }



        }

        short[] ConvertBytesToShorts(byte[] byteArray)
        {
            short[] shortArray = new short[byteArray.Length / 2];
            for (int i = 0; i < shortArray.Length; i++)
            {
                shortArray[i] = BitConverter.ToInt16(byteArray, i * 2);
            }
            return shortArray;
        }



    }
}

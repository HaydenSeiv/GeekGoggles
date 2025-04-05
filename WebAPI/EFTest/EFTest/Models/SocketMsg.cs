using DocumentFormat.OpenXml.Spreadsheet;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion.Internal;

namespace EFTest.Models
{
    public class SocketMsg
    {
        public string command { get; set; }
        public string message { get; set; }
        public string fileType { get; set; } = null;
        public string fileName { get; set; } = null;
        public string fileData { get; set; } = null;
        public string projName { get; set; }
        public int totalChunks { get; set; } = 0;
        public int chunkIndex { get; set; } = 0;

    }

    public class SocketMsgWeb
    {
        public string command { get; set; }
        public int user_id { get; set; }
        public int proj_id { get; set; }
        public string proj_name { get; set; } = null;
    }
}

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

        public int totalChunks { get; set; } = 0;
        public int chunkIndex { get; set; } = 0;

    }
}

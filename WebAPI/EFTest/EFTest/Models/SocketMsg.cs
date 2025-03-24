using Microsoft.EntityFrameworkCore.Storage.ValueConversion.Internal;

namespace EFTest.Models
{
    public class SocketMsg
    {
        public string Command { get; set; }
        public string Message { get; set; }
        public string FileName { get; set; } = null;
        public IFormFile File { get; set; } = null;
        public string FileType { get; set; } = null;
    }
}

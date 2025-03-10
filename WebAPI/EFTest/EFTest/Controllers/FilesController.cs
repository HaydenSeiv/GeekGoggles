using EFTest.Data;
using EFTest.Models;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace EFTest.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class FilesController : ControllerBase
    {
        private readonly AppDbContext _appDbContext;
        private readonly FileHandlerService _fileHandler;

        public FilesController(FileHandlerService fileHandler, AppDbContext appDbContext)
        {
            _fileHandler = fileHandler;
            _appDbContext = appDbContext;
        }

        //GetAll
        [HttpGet]
        public async Task<IActionResult> GetFiles()
        {
            var files = await _appDbContext.MyFiles.OrderBy(f=>f.Id).ToListAsync();
            return Ok(files);
        }

        //GetProjectFiles
        [HttpGet("getProjectFiles/{projID}")]
        public async Task<IActionResult> GetProjectFiles(int projID)
        {
            var files = await _fileHandler.GetProjectFilesAsync(projID);
            return Ok(files);
        }

        //GetProjectNoteFiles
        [HttpGet("getProjectFiles/Notes/{projID}")]
        public async Task<IActionResult> GetProjectNoteFiles(int projID)
        {
            var files = await _fileHandler.GetProjectNoteFilesAsync(projID);
            return Ok(files);
        }

        //GET
        [HttpGet("{id}")]
        public async Task<IActionResult> GetFile(int id)
        {
            try
            {
                var (fileContents, fileName) = await _fileHandler.GetFileAsync(id);
                return File(fileContents, fileName);
            }
            catch (FileNotFoundException)
            {
                return NotFound();
            }

        }

        //POST
        [HttpPost]
        public async Task<IActionResult> AddFile(IFormFile file, int projectId, string title, string customPath = null)
        {
            try
            {
                var sFile = await _fileHandler.SaveFileAsync(file, projectId, title, customPath, "document", "image");
                return Ok(sFile);
            }
            catch (Exception e)
            {
                return BadRequest(e);
            }
        }

        //DELETE
        [HttpDelete("{id}")]
        public async Task<IActionResult> DeleteFile(int id)
        {
            var res = await _fileHandler.DeleteFileAsync(id);
            return res ? Ok() : NoContent();

        }


    }
}

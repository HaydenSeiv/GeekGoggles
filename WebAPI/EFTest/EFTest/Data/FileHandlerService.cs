using EFTest.Data;
using EFTest.Models;
using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;
using System;
using System.IO;
using System.Threading.Tasks;


public class FileHandlerService
{
    private readonly AppDbContext _appDbContext;
    private readonly string _basePath;
    public Dictionary<string, string[]> _allowedFileTypes { get; private set; } //../

    public FileHandlerService(AppDbContext appDbContext, string basePath = "Client/uploads/myFiles")
    {
        _appDbContext = appDbContext;
        _basePath = basePath;


        // Initialize allowed file types
        _allowedFileTypes = new Dictionary<string, string[]>
        {
            // Documents
            { "document", new[] {
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document", // .docx
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // .xlsx
                "application/vnd.ms-powerpoint",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation" // .pptx
            }},
            
            // Images
            { "image", new[] {
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/bmp",
                "image/tiff",
                "image/webp"
            }},
            
            // Videos
            { "video", new[] {
                "video/mp4",
                "video/mpeg",
                "video/quicktime",
                "video/x-msvideo",
                "video/x-ms-wmv"
            }},
            
            // Audio
            { "audio", new[] {
                "audio/mpeg",
                "audio/wav",
                "audio/midi",
                "audio/x-midi",
                "audio/ogg",
                "audio/aac"
            }},
            
            // Archives
            { "archive", new[] {
                "application/zip",
                "application/x-rar-compressed",
                "application/x-7z-compressed",
                "application/x-tar",
                "application/gzip"
            }},
            
            // Text
            { "text", new[] {
                "text/plain",
                "text/csv",
                "text/html",
                "text/css",
                "text/javascript",
                "application/json",
                "application/xml"
            }}
        };

        //to ensure storage directory exists
        if (!Directory.Exists(_basePath))
        {
            Directory.CreateDirectory(_basePath);       //make one 
        }

    }

    /// <summary>
    /// check if filetype is among the acceptable files
    /// </summary>
    /// <param name="file"></param>
    /// <param name="fList"></param>
    /// <returns></returns>
    public bool IsTypeValid(IFormFile file, params string[] fList)
    {

        return fList.Any(type =>
        _allowedFileTypes.ContainsKey(type) &&
        _allowedFileTypes[type].Contains(file.ContentType.ToLower()));
    }


    /// <summary>
    /// save file in local directory and file details in the db
    /// </summary>
    /// <param name="file"></param>
    /// <param name="projName"></param>
    /// <param name="projectID"></param>
    /// <param name="title"></param>
    /// <param name="allowedTypes"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentException"></exception>
    /// <exception cref="Exception"></exception>
    public async Task<MyFilecs> SaveFileAsync(IFormFile file, int projectID, string title, string customPath = null, params string[] allowedTypes)
    {
        //chk if file is null
        if (file == null || file.Length == 0)
        {
            throw new ArgumentException("File can not empty");
        }

        //chk if file type is valid
        if (!IsTypeValid(file, allowedTypes))
        {
            throw new Exception($"File type is not valid {file.ContentType}");
        }

        //get proj Name
        var proj = await _appDbContext.Projects.FirstOrDefaultAsync(p => p.Id == projectID);
        var projName = proj.Title;
        
        //determine storage path
        string baseSavePath = customPath ?? _basePath;
        var projectPath = Path.Combine(baseSavePath, projName);
        if (!Directory.Exists(projectPath))
        {
            Directory.CreateDirectory(projectPath);
        }

        //generate file details
        var fileName = $"{Guid.NewGuid()}{Path.GetExtension(file.FileName)}";
        var filePath = Path.Combine(projectPath, fileName);
        var fileAddr = Path.Combine(projName, fileName).Replace("\\", "/");

        //save file to local directory
        using (var stream = new FileStream(filePath, FileMode.Create))
        {
            await file.CopyToAsync(stream);
        }

        //generate db item
        var nFile = new MyFilecs
        {
            Project = await _appDbContext.Projects.FirstOrDefaultAsync(p => p.Id == projectID),
            ProjectID = projectID,
            Title = title,
            FileType = file.ContentType,
            FileAddress = fileAddr
        };

        _appDbContext.Add(nFile);
        await _appDbContext.SaveChangesAsync();
        return nFile;
    }

    /// <summary>
    /// gets file name and its content in byte form 
    /// </summary>
    /// <param name="fileID"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentException"></exception>
    public async Task<(byte[] FileContents, string FileName)> GetFileAsync(int fileID)
    {
        //get file
        var mFile = await _appDbContext.MyFiles.FirstOrDefaultAsync(f => f.Id == fileID);

        //chk if file exists in db
        if (mFile == null)
        {
            throw new FileNotFoundException("File does not exist in DB");
        }

        //generate actual path
        var filePath = Path.Combine(_basePath, mFile.FileAddress);

        //chk if file is local directory
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException("File does not exists in local directory");
        }

        var fileContent = await File.ReadAllBytesAsync(filePath);
        var fileName = Path.GetFileName(mFile.FileAddress);
        return (fileContent, fileName);
    }

    /// <summary>
    /// deletes file from both local directory and database
    /// </summary>
    /// <param name="fileID"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentException"></exception>
    public async Task<bool> DeleteFileAsync(int fileID)
    {
        //get file
        var mFile = await _appDbContext.MyFiles.FirstOrDefaultAsync(f => f.Id == fileID);

        //chk if file exists in db
        if (mFile == null)
        {
            return false;
        }

        //generate actual path
        var filePath = Path.Combine(_basePath, mFile.FileAddress);

        //chk if file is local directory
        //if (!File.Exists(filePath))
        //{
        //    throw new ArgumentException("File does not exists in local directory");
        //}
        //else
        //{
            File.Delete(filePath);
        //}

        //remove from db
        _appDbContext.MyFiles.Remove(mFile);
        _appDbContext.SaveChangesAsync();

        return true;
    }

    /// <summary>
    /// gets all files in a project
    /// </summary>
    /// <param name="projectId"></param>
    /// <returns></returns>
    public async Task<List<MyFilecs>> GetProjectFilesAsync(int projectId)
    {
        return await _appDbContext.MyFiles
            .Where(f => f.ProjectID == projectId)
            .Where(f=> !f.Title.EndsWith("_Note.pdf"))
            .OrderByDescending(f => f.CreatedAt)
            .ToListAsync();
    }
}


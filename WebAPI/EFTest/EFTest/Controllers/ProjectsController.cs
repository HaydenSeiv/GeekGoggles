using EFTest.Data;
using EFTest.Models;
using EFTest.WebSockets;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using MQTTnet;
using MQTTnet.Adapter;
using MQTTnet.Server;
using Newtonsoft.Json;
using System.Net.Sockets;
using System.Text;

namespace EFTest.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ProjectsController : ControllerBase
    {
        private readonly AppDbContext _appDbContext;
        private readonly WebSocketHandler _webSocketHandler;
        private readonly IMqttServer _mqttServer;

        public ProjectsController(AppDbContext appDbContext, WebSocketHandler webSocketHandler, IMqttServer mqttServer)
        {
            _appDbContext = appDbContext;
            _webSocketHandler = webSocketHandler;
            _mqttServer = mqttServer;   
        }

        //GET All
        [HttpGet]
        public async Task<IActionResult> GetProjects()
        {
            var projects = await _appDbContext.Projects.ToListAsync();
            return Ok(projects);
        }
        //GET
        [HttpGet("{id}")]
        public async Task<IActionResult> GetProject(int id)
        {
            var project = await _appDbContext.Projects.FindAsync(id);
            if (project == null)
            {
                return NotFound();
            }
            return Ok(project);
        }
        //GET
        //gets all projects for a user
        [HttpGet("getUserProjects/{userId}")]
        public async Task<IActionResult> GetUserProjects(int userId)
        {
            var projects = await _appDbContext.Projects
                .Where(x => x.UserID == userId)
                .ToListAsync();

            //if (!projects.Any())
            //{
            //    return NotFound();
            //}

            if (projects.Count() == 0)
            {
                return NoContent();
            }
            return Ok(projects);
        }

        //POST
        //creates a new project in the database
        [HttpPost]
        public async Task<IActionResult> AddProject([FromBody] ProjectCreator p)
        {
            Console.WriteLine("Creating Project");

            //if (!ModelState.IsValid)
            //    return BadRequest(ModelState);

            if (p == null)
                return BadRequest("Project data is required.");

            //check if the User exists
            var user = _appDbContext.Users.Find(p.UserId);
            if (user == null)
                return NotFound("User not found.");

            Project project = new Project();

            project.User = user;  // Attach the user to the project
            project.Title = p.Title;
            project.UserID = p.UserId;

            _appDbContext.Projects.Add(project);
            await _appDbContext.SaveChangesAsync();

            Console.WriteLine($"Project {project.Title} Created");
            return Ok(project);
        }
        //PUT
        [HttpPut("{id}")]
        public async Task<IActionResult> EditProject(int id, Project project)
        {
            if (id != project.Id)
            {
                return BadRequest();
            }

            //update user in the db
            _appDbContext.Entry(project).State = EntityState.Modified;
            await _appDbContext.SaveChangesAsync();
            return NoContent();
        }

        //DELETE
        [HttpDelete("deleteProject/{id}")]
        public async Task<IActionResult> DeleteProject(int id)
        {
            //find user
            var project = await _appDbContext.Projects.FindAsync(id);

            if (project == null)
            {
                return NotFound();
            }
            _appDbContext.Projects.Remove(project);
            await _appDbContext.SaveChangesAsync();

            return NoContent();

        }

        [HttpPost("/project/info/{id}")]
        public async Task<IActionResult> SendProjInfo(int id)
        {
            //find project
            var proj = await _appDbContext.Projects.FindAsync(id);
            if (proj == null)
                return NotFound("Project not found");

            //find user
            var user =  await _appDbContext.Users.FindAsync(proj.UserID);
            if (user == null)
                return NotFound("User not found");

            var message = JsonConvert.SerializeObject(new SocketMsgWeb
            {
                command = "login_info",
                user_id = user.Id,
                proj_id = proj.Id,
                proj_name = proj.Title
            });

            var msgBytes = Encoding.UTF8.GetBytes(message);
            try
            {
                await _webSocketHandler.BroadCastMessageAsync(message);
                Console.WriteLine("Sent Project Info to Pi");
                //await _mqttServer.

            }
            catch (SocketException)
            {
                Console.WriteLine($"SocketExpection while sending Project Info");
                return StatusCode(500, "Error while Sending Project Info");
            }
            catch(Exception ex)
            {
                Console.WriteLine($"Expection while sending Project Info");
                return StatusCode(500, $"Error while Sending Project Info - REST");
            }

            return Ok(new { message = "Project Info Broadcasted successful" });
        }

        // Class used to get project data from the client to create a new project
        public class ProjectCreator
        {
            public string Title { get; set; }
            public int UserId { get; set; }
        }

    }
}

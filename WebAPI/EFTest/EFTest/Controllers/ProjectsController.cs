using EFTest.Data;
using EFTest.Models;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace EFTest.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ProjectsController : ControllerBase
    {
        private readonly AppDbContext _appDbContext;

        public ProjectsController(AppDbContext appDbContext)
        {
            _appDbContext = appDbContext;
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

            if(projects.Count() == 0)
            {
                return NoContent();
            }
            return Ok(projects);
        }

        //POST
        //creates a new project in the database
        [HttpPost]
        public async Task<IActionResult> AddProject([FromBody]ProjectCreator p)
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

        // Class used to get project data from the client to create a new project
        public class ProjectCreator
        {
            public string Title { get; set; }
            public int UserId { get; set; }
        }

    }
}

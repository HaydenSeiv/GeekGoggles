using EFTest.Data;
using EFTest.Models;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace EFTest.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ReadingsController : ControllerBase
    {
        private readonly AppDbContext _appDbContext;
        public ReadingsController(AppDbContext appDbContext)
        {
            _appDbContext = appDbContext;
        }

        //GET All
        [HttpGet]
        public async Task<IActionResult> GetReadings()
        {
            var reading = await _appDbContext.Readings.ToListAsync();
            return Ok(reading);
        }
        //GET
        [HttpGet("{id}")]
        public async Task<IActionResult> GetReading(int id)
        {
            var reading = await _appDbContext.Readings.FindAsync(id);
            if (reading == null)
            {
                return NotFound();
            }
            return Ok(reading);
        }

        //POST
        [HttpPost]
        public async Task<IActionResult> Addreading(Reading reading)
        {
            if (reading == null)
                return BadRequest("Project data is required.");

            //check if the Project exists
            var proj = _appDbContext.Projects.Find(reading.ProjectID);
            if (proj == null)
                return NotFound("Project not found.");

            reading.Project = proj;  // Attach the user to the project

            _appDbContext.Readings.Add(reading);
            await _appDbContext.SaveChangesAsync();

            return Ok(reading);
        }
        //PUT
        [HttpPut("{id}")]
        public async Task<IActionResult> Editreading(int id, Reading reading)
        {
            if (id != reading.Id)
            {
                return BadRequest();
            }

            //update user in the db
            _appDbContext.Entry(reading).State = EntityState.Modified;
            await _appDbContext.SaveChangesAsync();
            return NoContent();
        }

        //DELETE
        [HttpDelete("{id}")]
        public async Task<IActionResult> Deletereading(int id)
        {
            //find user
            var reading = await _appDbContext.Readings.FindAsync(id);

            if (reading == null)
            {
                return NotFound();
            }
            _appDbContext.Readings.Remove(reading);
            await _appDbContext.SaveChangesAsync();

            return NoContent();

        }
    }
}

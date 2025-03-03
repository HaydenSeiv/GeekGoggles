using EFTest.Data;
using EFTest.Models;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.JsonPatch;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace EFTest.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class NotesController : ControllerBase
    {
        private readonly AppDbContext _appDbContext;

        public NotesController(AppDbContext appDbContext)
        {
            _appDbContext = appDbContext;
        }

        //GET All
        [HttpGet]
        public async Task<IActionResult> GetNotes()
        {
            var notes = await _appDbContext.Notes.ToListAsync();
            return Ok(notes);
        }
        //GET
        [HttpGet("{id}")]
        public async Task<IActionResult> Getnote(int id)
        {
            var note = await _appDbContext.Notes.FindAsync(id);
            if (note == null)
            {
                return NotFound();
            }
            return Ok(note);
        }

        [HttpGet("getProjectNotes/{projID}")]
        public async Task<IActionResult> GetProjectNotes(int projID)
        {
            var notes = await _appDbContext.Notes.Where(i => i.ProjectID == projID).ToListAsync();
            //if (notes == null)
            //{
            //    return NoContent();
            //}
            if (notes.Count() == 0)
            {
                return NoContent();
            }
            return Ok(notes);
        }

        //POST
        [HttpPost]
        public async Task<IActionResult> Addnote([FromBody]NoteCreator n)
        {
            if (n == null)
                return BadRequest("Note data is required.");

            //check if the Project exists
            var proj = _appDbContext.Projects.Find(n.ProjectId);
            if (proj == null)
                return NotFound("Project not found.");
            Note note = new Note();
            note.Project = proj;  // Attach the project to the note
            note.Title = n.Title;
            note.NoteBody = n.NoteBody;

            _appDbContext.Notes.Add(note);
            await _appDbContext.SaveChangesAsync();

            return Ok(note);
        }
        //PUT
        [HttpPut("{id}")]
        public async Task<IActionResult> Editnote(int id, [FromBody] Note note)
        {
            if (id != note.Id)
            {
                return BadRequest("ID mismatch.");
            }

            var existingNote = await _appDbContext.Notes.FindAsync(id);
            if (existingNote == null)
            {
                return NotFound();
            }

            existingNote.Title = note.Title;
            existingNote.NoteBody = note.NoteBody;
            if(existingNote.Project == null)
            {
                existingNote.ProjectID = note.ProjectID;
            }


            await _appDbContext.SaveChangesAsync();
            return NoContent();
        }

        //PATCH
        [HttpPatch("{id}")]
        public async Task<IActionResult> UpdateNote(int id, [FromBody] JsonPatchDocument<Note> patch)
        {
            if(patch == null)
            {
                return BadRequest();
            }

            var existingNote = await _appDbContext.Notes.FindAsync(id);
            if(existingNote == null)
            {
                return NotFound();
            }

            patch.ApplyTo(existingNote, ModelState);

            if (!ModelState.IsValid)
            {
                return BadRequest();
            }

            await _appDbContext.SaveChangesAsync();
            return NoContent();
        }

        //DELETE
        [HttpDelete("{id}")]
        public async Task<IActionResult> Deletenote(int id)
        {
            //find user
            var note = await _appDbContext.Notes.FindAsync(id);

            if (note == null)
            {
                return NotFound();
            }
            _appDbContext.Notes.Remove(note);
            await _appDbContext.SaveChangesAsync();

            return NoContent();

        }


        // Class used to get notes data from the client to create a new note
        public class NoteCreator
        {
            public string Title { get; set; }
            public int ProjectId { get; set; }

            public string NoteBody { get; set; }
        }

    }
}

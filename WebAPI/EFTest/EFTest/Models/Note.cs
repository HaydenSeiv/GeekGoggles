using Microsoft.EntityFrameworkCore;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace EFTest.Models
{
    public class Note
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]  // enables auto-increment
        public int Id { get; set; } //primary key

        [ForeignKey("Project")]
        public int ProjectID { get; set; } //foreing key

        [Required]
        public string Title { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;  //set cur time to now 

        public Project Project { get; set; }  //connection to Project

        public string NoteBody { get; set; } //add NoteBody
    }
}

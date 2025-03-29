using Microsoft.EntityFrameworkCore;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace EFTest.Models
{
    public class Note
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]  
        public int Id { get; set; } //PK

        [ForeignKey("Project")]
        public int ProjectID { get; set; } //FK

        [Required]
        public string Title { get; set; }
        public string NoteBody { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        //Navigation Property
        public Project Project { get; set; }

    }
}

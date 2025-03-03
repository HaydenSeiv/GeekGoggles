using Microsoft.EntityFrameworkCore;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace EFTest.Models
{
    public class Project
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]  // enables auto-increment
        public int Id { get; set; } //primary key

        [ForeignKey("User")]
        public int UserID { get; set; } //foreing key

        [Required]
        public string Title { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;  //set cur time to now 

        public User User { get; set; }  //connection to User


    }
}

using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;

namespace EFTest.Models
{
    public class User
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]  // enables auto-increment
        public int Id { get; set; } //primary key
        
        public string UserName { get; set; } //User Name
        public string FirstName { get; set; }
        public string LastName { get; set; }
        public string Email { get; set; }
        public string PasswordHash { get; set; }        //store pass as hash
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;  //set cur time to now 

    }
}

using EFTest.Data;
using EFTest.Models;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Identity;

namespace EFTest.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class UsersController : ControllerBase
    {
        private readonly AppDbContext _appDbContext;

        //used to hash passwords, uses "Microsoft.AspNetCore.Identity"
        private readonly IPasswordHasher<User> _passwordHasher; //for password hashing

        public UsersController(AppDbContext appDbContext, IPasswordHasher<User> passwordHasher  )
        {
            _appDbContext = appDbContext;
            _passwordHasher = passwordHasher;
        }


        [HttpOptions]
        [Route("api/Users")]
        public IActionResult Options()
        {
            return Ok();
        }

        //GET All
        [HttpGet]
        public async Task<IActionResult> GetUsers()
        {
            var users = await _appDbContext.Users.ToListAsync();
            return Ok(users);
        }
        //GET
        [HttpGet("{id}")]
        public async Task<IActionResult> GetUser(int id)
        {
            var user = await _appDbContext.Users.FindAsync(id);
            if (user == null)
            {
                return NotFound();
            }
            return Ok(user);
        }

        //POST
        //used to create a new user, gets username, password, first name, last name, and email from the registration page on client side
        [HttpPost]
        public async Task<IActionResult> AddUser(User user)
        {
            // Check if username already exists
            if (await _appDbContext.Users.AnyAsync(u => u.UserName == user.UserName))
            {
                return BadRequest("Username already exists");
            }

            //check if email already exists
            if (await _appDbContext.Users.AnyAsync(u => u.Email == user.Email))
            {
                return BadRequest("Email already exists");
            }

            // Hash the password
            user.PasswordHash = _passwordHasher.HashPassword(user, user.PasswordHash);

            // Add the new user
            _appDbContext.Users.Add(user);
            await _appDbContext.SaveChangesAsync();

            //return the user info to the client 
            return CreatedAtAction(
                nameof(GetUser),
                new { id = user.Id },
                new
                {
                    user.Id,
                    user.UserName,
                    user.FirstName,
                    user.LastName,
                    user.Email
                }
            );
        }

        //PUT
        [HttpPut("{id}")]
        public async Task<IActionResult> EditUser(int id, User user)
        {
            if (id != user.Id)
            {
                return BadRequest();
            }

            //update user in the db
            _appDbContext.Entry(user).State = EntityState.Modified;
            await _appDbContext.SaveChangesAsync();
            return NoContent();
        }

        //DELETE
        [HttpDelete("{id}")]
        public async Task<IActionResult> DeleteUser(int id)
        {
            //find user
            var user = await _appDbContext.Users.FindAsync(id);

            if(user == null)
            {
                return NotFound();
            }
            _appDbContext.Users.Remove(user);
            await _appDbContext.SaveChangesAsync();

            return NoContent();

        }

        //POST
        //used to login a user, gets username and password from login page on the client side
        //this is then stored in session storage on the client side to track the user
        [HttpPost("Login")]
        public async Task<IActionResult> Login([FromBody] LoginRequest request)
        {
            // Find user by username
            var user = await _appDbContext.Users
                .FirstOrDefaultAsync(u => u.UserName == request.Username);

            if (user == null)
            {
                return Unauthorized("Invalid username or password");
            }

            // Verify password
            if (!VerifyPassword(user, request.Password))
            {
                return Unauthorized("Invalid username or password");
            }

            // Return user info - stored in session storage on the client side
            return Ok(new
            {
                user.Id,
                user.UserName,
                user.FirstName,
                user.LastName,
                user.Email
            });
        }

        // Class used to get username and password from the client for login
        public class LoginRequest
        {
            public string Username { get; set; }
            public string Password { get; set; }
        }

        // function to verify password using the password hasher in "Microsoft.AspNetCore.Identity"
        private bool VerifyPassword(User user, string providedPassword)
        {
            var result = _passwordHasher.VerifyHashedPassword(
                user,
                user.PasswordHash,  // stored hash
                providedPassword  // provided password
            );
            
            return result == PasswordVerificationResult.Success;
        }
    }
}

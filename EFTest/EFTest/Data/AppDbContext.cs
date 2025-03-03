using EFTest.Models;
using Microsoft.EntityFrameworkCore;

namespace EFTest.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions options): base(options) { }
        

        public DbSet<Product> Products { get; set; }
    }
}

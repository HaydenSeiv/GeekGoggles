using EFTest.Models;
using Microsoft.EntityFrameworkCore;

namespace EFTest.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions options) : base(options) { }


        public DbSet<User> Users { get; set; }

        public DbSet<Project> Projects { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<Project>()
                .HasOne(p => p.User)
                .WithMany() //connect one-to-many for User-Projects
                .HasForeignKey(p => p.UserID)
                .OnDelete(DeleteBehavior.Cascade);      //deletes all proj connected to user when user is deleted 

            modelBuilder.Entity<Note>()
             .HasOne(p => p.Project)
             .WithMany() //connect one-to-many for Projects-Note
             .HasForeignKey(p => p.ProjectID)
             .OnDelete(DeleteBehavior.Cascade);      //deletes all notes connected to proj when proj is deleted 

            modelBuilder.Entity<Reading>()
             .HasOne(p => p.Project)
             .WithMany() //connect one-to-many for Projects-Reading
             .HasForeignKey(p => p.ProjectID)
             .OnDelete(DeleteBehavior.Cascade);      //deletes all notes connected to proj when proj is deleted  

            modelBuilder.Entity<MyFilecs>()
             .HasOne(p => p.Project)
             .WithMany() //connect one-to-many for Projects-Files
             .HasForeignKey(p => p.ProjectID)
             .OnDelete(DeleteBehavior.Cascade);     //deletes all files connected to proj when proj is deleted 
        }

        public DbSet<Note> Notes { get; set; }

        public DbSet<Reading> Readings { get; set; }

        public DbSet<MyFilecs> MyFiles { get; set; }



    }
}

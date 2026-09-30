using System.Text;
using HiMarket.Application.Interfaces;
using HiMarket.Infrastructure.Persistence;
using HiMarket.Infrastructure.Services;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;

var builder = WebApplication.CreateBuilder(args);

// 1. Add Controllers & OpenAPI/Swagger
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo
    {
        Title = "HiMarket API",
        Version = "v1",
        Description = "Hİ MARKET Kurumsal Satış & Kasa Otomasyonu REST API"
    });
});

// 2. Add DbContext (SQLite for easy portability & zero config)
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection") 
                       ?? "Data Source=himarket.db";

builder.Services.AddDbContext<HiMarketDbContext>(options =>
    options.UseSqlite(connectionString));

// 3. Register Application Services
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddScoped<IShiftService, ShiftService>();
builder.Services.AddScoped<ISaleService, SaleService>();

// 4. Configure CORS for Python Django Frontend
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

// 5. Configure JWT Authentication
var jwtSecret = builder.Configuration["Jwt:Secret"] ?? "HiMarket_Secret_Key_Super_Secure_2026_Commercial_App!";
var key = Encoding.UTF8.GetBytes(jwtSecret);

builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.RequireHttpsMetadata = false;
    options.SaveToken = true;
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuerSigningKey = true,
        IssuerSigningKey = new SymmetricSecurityKey(key),
        ValidateIssuer = false,
        ValidateAudience = false
    };
});

var app = builder.Build();

// 6. Auto-Migrate & Seed Database on Startup
using (var scope = app.Services.CreateScope())
{
    var context = scope.ServiceProvider.GetRequiredService<HiMarketDbContext>();
    await DbInitializer.SeedAsync(context);
}

// 7. Configure HTTP Request Pipeline
app.UseSwagger(c =>
{
    c.SerializeAsV2 = true;
});
app.UseSwaggerUI(c =>
{
    c.SwaggerEndpoint("/swagger/v1/swagger.json", "HiMarket API v1");
});

app.UseCors("AllowAll");
app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

// Otomatik Swagger yönlendirmeleri (Kök dizin ve olası klavye yazım hataları)
app.MapGet("/", () => Results.Redirect("/swagger"));
app.MapGet("/swaqqer", () => Results.Redirect("/swagger"));
app.MapGet("/swaqqer/index.html", () => Results.Redirect("/swagger/index.html"));

app.Run();

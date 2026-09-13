using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Application.Models.Authentication;
using ForexIntelligence.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace ForexIntelligence.Infrastructure.Repositories;

public sealed class UserRepository(ForexDbContext dbContext) : IUserRepository
{
    public async Task<UserCredential?> GetByUsernameAsync(
        string username,
        CancellationToken cancellationToken)
    {
        return await dbContext.Users
            .AsNoTracking()
            .Where(user => user.Username == username)
            .Select(user => new UserCredential(
                user.Id,
                user.Username,
                user.PasswordHash,
                user.Role,
                user.IsActive))
            .SingleOrDefaultAsync(cancellationToken);
    }
}

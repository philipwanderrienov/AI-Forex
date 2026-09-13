using ForexIntelligence.Application.Models.Authentication;

namespace ForexIntelligence.Application.Interfaces.Repositories;

public interface IUserRepository
{
    Task<UserCredential?> GetByUsernameAsync(
        string username,
        CancellationToken cancellationToken);
}

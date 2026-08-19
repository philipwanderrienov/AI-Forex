using System.Globalization;
using System.Security.Cryptography;

namespace ForexIntelligence.Api.Authentication;

public static class PasswordHashing
{
    private const int Iterations = 210_000;
    private const int SaltSize = 16;
    private const int HashSize = 32;
    private const string Algorithm = "pbkdf2-sha256";

    public static string Hash(string password)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(password);
        var salt = RandomNumberGenerator.GetBytes(SaltSize);
        var hash = Rfc2898DeriveBytes.Pbkdf2(
            password,
            salt,
            Iterations,
            HashAlgorithmName.SHA256,
            HashSize);
        return string.Join(
            '$',
            Algorithm,
            Iterations.ToString(CultureInfo.InvariantCulture),
            Convert.ToBase64String(salt),
            Convert.ToBase64String(hash));
    }

    public static bool Verify(string password, string encodedHash)
    {
        if (!TryParse(encodedHash, out var iterations, out var salt, out var expectedHash))
        {
            return false;
        }

        var actualHash = Rfc2898DeriveBytes.Pbkdf2(
            password,
            salt,
            iterations,
            HashAlgorithmName.SHA256,
            expectedHash.Length);
        return CryptographicOperations.FixedTimeEquals(actualHash, expectedHash);
    }

    public static bool IsValidHash(string encodedHash) =>
        TryParse(encodedHash, out _, out _, out _);

    private static bool TryParse(
        string encodedHash,
        out int iterations,
        out byte[] salt,
        out byte[] hash)
    {
        iterations = 0;
        salt = [];
        hash = [];
        var parts = encodedHash.Split('$', StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length != 4
            || parts[0] != Algorithm
            || !int.TryParse(parts[1], CultureInfo.InvariantCulture, out iterations)
            || iterations < 100_000)
        {
            return false;
        }

        try
        {
            salt = Convert.FromBase64String(parts[2]);
            hash = Convert.FromBase64String(parts[3]);
            return salt.Length >= SaltSize && hash.Length >= HashSize;
        }
        catch (FormatException)
        {
            return false;
        }
    }
}

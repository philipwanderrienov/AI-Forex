using ForexIntelligence.Api.Authentication;

namespace ForexIntelligence.IntegrationTests;

public sealed class PasswordHashingTests
{
    [Fact]
    public void Hash_CreatesVerifiableNonPlaintextValue()
    {
        const string password = "correct horse battery staple";

        var hash = PasswordHashing.Hash(password);

        Assert.NotEqual(password, hash);
        Assert.True(PasswordHashing.IsValidHash(hash));
        Assert.True(PasswordHashing.Verify(password, hash));
        Assert.False(PasswordHashing.Verify("wrong password", hash));
    }

    [Theory]
    [InlineData("")]
    [InlineData("plaintext")]
    [InlineData("pbkdf2-sha256$1$invalid$invalid")]
    public void IsValidHash_RejectsMalformedOrWeakValue(string value)
    {
        Assert.False(PasswordHashing.IsValidHash(value));
    }
}

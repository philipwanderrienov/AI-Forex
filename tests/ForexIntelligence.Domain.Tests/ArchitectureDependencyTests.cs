using ForexIntelligence.Domain.Entities;

namespace ForexIntelligence.Domain.Tests;

public sealed class ArchitectureDependencyTests
{
    [Fact]
    public void Domain_does_not_reference_other_solution_layers()
    {
        var forbiddenReferences = new HashSet<string>(StringComparer.Ordinal)
        {
            "ForexIntelligence.Api",
            "ForexIntelligence.Application",
            "ForexIntelligence.Infrastructure",
            "ForexIntelligence.Worker"
        };

        var actualReferences = typeof(Candle).Assembly
            .GetReferencedAssemblies()
            .Select(reference => reference.Name)
            .Where(name => name is not null)
            .Cast<string>();

        Assert.Empty(actualReferences.Intersect(forbiddenReferences, StringComparer.Ordinal));
    }
}

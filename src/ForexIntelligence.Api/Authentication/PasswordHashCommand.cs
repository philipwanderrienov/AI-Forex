namespace ForexIntelligence.Api.Authentication;

public static class PasswordHashCommand
{
    public static int Run()
    {
        Console.Write("Password: ");
        var password = Console.IsInputRedirected ? Console.ReadLine() : ReadMaskedPassword();
        Console.WriteLine();

        if (string.IsNullOrWhiteSpace(password))
        {
            Console.Error.WriteLine("Password tidak boleh kosong.");
            return 1;
        }

        Console.WriteLine(PasswordHashing.Hash(password));
        return 0;
    }

    private static string ReadMaskedPassword()
    {
        var characters = new List<char>();
        while (true)
        {
            var key = Console.ReadKey(intercept: true);
            if (key.Key == ConsoleKey.Enter)
            {
                return new string([.. characters]);
            }

            if (key.Key == ConsoleKey.Backspace && characters.Count > 0)
            {
                characters.RemoveAt(characters.Count - 1);
                continue;
            }

            if (!char.IsControl(key.KeyChar))
            {
                characters.Add(key.KeyChar);
            }
        }
    }
}

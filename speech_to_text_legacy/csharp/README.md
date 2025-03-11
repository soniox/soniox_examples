# Soniox C# client library examples

### Requirements

.NET 6 or newer.

### How to run

Set your Soniox Cloud API key:

```
export SONIOX_API_KEY=<YOUR_API_KEY>
```

Run an example:

```
cd TranscribeFileShort
dotnet run
```

### How to use in your project

The Soniox C# client library is published on NuGet:
[Soniox.Client](https://www.nuget.org/packages/Soniox.Client/).
To use the library in your project, add package references to the
`.csproj` file like in the examples:

```
<PackageReference Include="Google.Protobuf" Version="3.22.1" />
<PackageReference Include="Soniox.Client" Version="1.1.0" />
```

You can specify the Soniox API key in the Client constructor instead
of using an environment variable:

```
using var client = new SpeechClient(apiKey: ...);
```

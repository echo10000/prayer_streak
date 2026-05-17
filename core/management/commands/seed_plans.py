from django.core.management.base import BaseCommand

from core.models import BibleReadingPlan, BibleReadingPlanDay


class Command(BaseCommand):
    help = "Seed starter Bible reading plans."

    def handle(self, *args, **options):
        plans = [
            {
                "title": "7 Days of Gratitude",
                "days": 7,
                "theme": "Gratitude",
                "description": "A one-week rhythm of thanksgiving, contentment, and noticing God's gifts.",
                "days_data": [
                    ("Psalm 100:4", "Enter With Thanksgiving", "Enter his gates with thanksgiving and his courts with praise; give thanks to him and praise his name.", "Gratitude begins by entering God's presence with open hands. Today, name the gifts you have rushed past.", "Lord, open my eyes to Your goodness and teach me to come before You with thanksgiving."),
                    ("1 Thessalonians 5:18", "Give Thanks in Everything", "Give thanks in all circumstances; for this is God's will for you in Christ Jesus.", "Thankfulness does not deny difficulty. It anchors the heart in God's faithfulness inside every circumstance.", "Father, help me practice gratitude even when today feels unfinished or heavy."),
                    ("Colossians 3:15", "Let Peace Rule", "Let the peace of Christ rule in your hearts... And be thankful.", "Peace and gratitude grow together. A thankful heart becomes more available to the rule of Christ.", "Jesus, let Your peace govern my reactions and make my heart thankful."),
                    ("Philippians 4:6", "Bring Everything to God", "Do not be anxious about anything, but in every situation, by prayer and petition, with thanksgiving, present your requests to God.", "Prayer carries anxiety into God's care. Thanksgiving reminds the soul who is receiving the burden.", "Lord, I bring You my worries with thanksgiving for Your nearness."),
                    ("Psalm 107:1", "His Love Endures", "Give thanks to the Lord, for he is good; his love endures forever.", "God's goodness is not seasonal. His love outlasts the moment you are standing in.", "God, steady me in Your enduring love and make praise my first response."),
                    ("James 1:17", "Every Good Gift", "Every good and perfect gift is from above, coming down from the Father of the heavenly lights.", "Gratitude traces gifts back to the Giver. Today, receive small mercies as signs of the Father's care.", "Father, help me receive every good gift with humility and joy."),
                    ("Psalm 136:1", "Forever Mercy", "Give thanks to the Lord, for he is good. His love endures forever.", "The refrain of God's love is worth repeating until your heart remembers it under pressure.", "Lord, write Your enduring mercy into the rhythm of my day."),
                ],
            },
            {
                "title": "Lenten Journey",
                "days": 40,
                "theme": "Lent",
                "description": "A 40-day journey of repentance, sacrifice, and drawing near to God. The first seven days are seeded; add the remaining days in admin.",
                "days_data": [
                    ("Psalm 51:10", "Create in Me a Clean Heart", "Create in me a clean heart, O God, and renew a steadfast spirit within me.", "Lent begins with honesty before God. Renewal starts when we stop pretending we can cleanse ourselves.", "Lord, create in me a clean heart and renew my desires."),
                    ("Isaiah 58:6", "The Fast God Chooses", "Is not this the kind of fasting I have chosen: to loose the chains of injustice...", "Sacrifice is not performance. God-shaped fasting opens our hands toward mercy and justice.", "Father, make my sacrifice fruitful in love for others."),
                    ("Psalm 130:5", "Wait for the Lord", "I wait for the Lord, my whole being waits, and in his word I put my hope.", "Waiting is holy work when hope is placed in God's Word.", "Lord, teach me to wait without losing hope."),
                    ("Isaiah 55:6", "Seek Him While Near", "Seek the Lord while he may be found; call on him while he is near.", "Lent invites us to return while grace is calling.", "God, draw me back wherever my heart has drifted."),
                    ("Psalm 32:5", "Confession and Mercy", "Then I acknowledged my sin to you... and you forgave the guilt of my sin.", "Confession is not a doorway to shame. It is a doorway to mercy.", "Lord, give me courage to confess and faith to receive forgiveness."),
                    ("Isaiah 53:5", "By His Wounds", "But he was pierced for our transgressions... and by his wounds we are healed.", "The cross reveals the cost of love and the depth of healing God offers.", "Jesus, keep me near the cross and humble before Your love."),
                    ("Psalm 42:1", "Thirst for God", "As the deer pants for streams of water, so my soul pants for you, my God.", "Fasting uncovers thirst. Let that hunger point you back to God.", "Lord, awaken my longing for You above every lesser comfort."),
                ],
            },
            {
                "title": "New Believer Basics",
                "days": 14,
                "theme": "Foundations",
                "description": "Foundational Scriptures for new Christians learning the promises, practices, and hope of following Jesus.",
                "days_data": [
                    ("John 3:16", "God So Loved", "For God so loved the world that he gave his one and only Son...", "The Christian life begins with God's initiating love, not our achievement.", "Father, help me receive Your love through Jesus with trust."),
                    ("Romans 8:28", "God Works for Good", "And we know that in all things God works for the good of those who love him...", "God is able to weave even confusing seasons into His redemptive purpose.", "Lord, teach me to trust Your work when I cannot see the whole picture."),
                    ("Jeremiah 29:11", "Hope and Future", "For I know the plans I have for you... plans to give you hope and a future.", "God's plans are rooted in His faithful character.", "God, help me walk into Your future with patience and hope."),
                    ("2 Corinthians 5:17", "New Creation", "If anyone is in Christ, the new creation has come: The old has gone, the new is here!", "In Christ, your identity is not chained to your past.", "Jesus, teach me to live from my new identity in You."),
                    ("Ephesians 2:8-9", "Saved by Grace", "For it is by grace you have been saved, through faith... not by works.", "Grace is a gift. You do not earn your way into God's family.", "Lord, root my faith in grace instead of striving."),
                    ("Matthew 6:33", "Seek First", "But seek first his kingdom and his righteousness...", "Following Jesus reorders desire, priority, and daily choices.", "Father, make Your kingdom my first pursuit."),
                    ("Philippians 4:13", "Strength in Christ", "I can do all this through him who gives me strength.", "Christian strength is dependence on Christ, not self-confidence.", "Christ, strengthen me to obey You today."),
                    ("Proverbs 3:5-6", "Trust the Lord", "Trust in the Lord with all your heart and lean not on your own understanding...", "Trust means bringing your understanding under God's guidance.", "Lord, direct my path as I trust You."),
                    ("Galatians 5:22-23", "Fruit of the Spirit", "The fruit of the Spirit is love, joy, peace, forbearance, kindness...", "Spiritual growth is fruit produced by the Spirit's life in you.", "Holy Spirit, grow Your fruit in my ordinary choices."),
                    ("1 John 1:9", "Forgiven and Cleansed", "If we confess our sins, he is faithful and just and will forgive us...", "Confession keeps fellowship open and honest before God.", "Lord, make me quick to confess and confident in Your mercy."),
                    ("Matthew 28:19-20", "Make Disciples", "Therefore go and make disciples of all nations...", "Every believer is invited into God's mission of witness and love.", "Jesus, help me follow You and point others toward You."),
                    ("Hebrews 10:24-25", "Gather Together", "Let us consider how we may spur one another on toward love and good deeds...", "Faith grows in community, encouragement, and shared worship.", "Lord, plant me in faithful community."),
                    ("Psalm 119:105", "Lamp to My Feet", "Your word is a lamp for my feet, a light on my path.", "Scripture gives enough light for faithful next steps.", "God, light my path through Your Word."),
                    ("Romans 12:1", "A Living Sacrifice", "Offer your bodies as a living sacrifice, holy and pleasing to God...", "Worship is the offering of your whole life to God.", "Lord, receive my life as worship today."),
                ],
            },
        ]

        for plan_data in plans:
            days_data = plan_data.pop("days_data")
            plan, _ = BibleReadingPlan.objects.update_or_create(
                title=plan_data["title"],
                defaults=plan_data,
            )
            for index, (reference, title, text, reflection, prayer_prompt) in enumerate(days_data, start=1):
                BibleReadingPlanDay.objects.update_or_create(
                    plan=plan,
                    day_number=index,
                    defaults={
                        "title": title,
                        "passage_reference": reference,
                        "passage_text": text,
                        "reflection": reflection,
                        "prayer_prompt": prayer_prompt,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Seeded Bible reading plans."))

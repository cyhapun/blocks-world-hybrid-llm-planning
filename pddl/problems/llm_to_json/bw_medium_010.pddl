(define (problem bw_medium_010)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table a)
    (on_table c)
    (on b a)
    (on d b)
    (clear d)
    (clear c)
    (handempty)
  )

  (:goal
    (on c d)
  )
)
